"""
License Server - Manage bot licenses and authentication.
"""

import jwt
import hashlib
import secrets
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class LicenseServer:
    """Server-side license management and validation."""

    def __init__(self, secret_key: Optional[str] = None, db_path: str = "licenses.db"):
        self.secret_key = secret_key or Fernet.generate_key().decode()
        self.db_path = Path(db_path)
        self.licenses: Dict[str, Dict[str, Any]] = {}
        self._load_licenses()

    def _load_licenses(self):
        """Load licenses from the database file."""
        if not self.db_path.exists():
            logger.info("No existing license database found, starting fresh.")
            self.licenses = {}
            return

        try:
            with self.db_path.open("r", encoding="utf-8") as f:
                self.licenses = json.load(f)
            logger.info("Loaded %d licenses from database.", len(self.licenses))
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load license database: %s", e)
            self.licenses = {}

    def _save_licenses(self):
        """Persist licenses to the database file."""
        try:
            with self.db_path.open("w", encoding="utf-8") as f:
                json.dump(self.licenses, f, indent=2, ensure_ascii=False)
            logger.debug("License database saved successfully.")
        except Exception as e:
            logger.exception("Failed to save license database: %s", e)
            raise

    def generate_license_key(self, user_id: str, duration_days: int = 2) -> str:
        """
        Generate a new license key for a user.

        Args:
            user_id: Unique identifier for the user.
            duration_days: License validity period in days.

        Returns:
            str: Generated license key.
        """
        if duration_days <= 0:
            raise ValueError("License duration must be positive.")

        license_key = secrets.token_urlsafe(32)
        expiry_date = datetime.now() + timedelta(days=duration_days)

        license_data = {
            "user_id": user_id,
            "license_key": license_key,
            "created_at": datetime.now().isoformat(),
            "expires_at": expiry_date.isoformat(),
            "duration_days": duration_days,
            "status": "active",
            "hardware_id": None,
            "activations": 0,
            "max_activations": 1,
        }

        self.licenses[license_key] = license_data
        self._save_licenses()
        logger.info("Generated license for user '%s' valid for %d days.", user_id, duration_days)
        return license_key

    def verify_license(self, license_key: str, hardware_id: str) -> Dict[str, Any]:
        """
        Verify a license key with hardware binding.

        Args:
            license_key: License key to verify.
            hardware_id: Unique hardware identifier.

        Returns:
            dict: Verification result containing validity and token info.
        """
        license_data = self.licenses.get(license_key)
        if not license_data:
            logger.warning("License verification failed: invalid key '%s...'", license_key[:8])
            return {"valid": False, "message": "Invalid license key", "token": None}

        if license_data["status"] == "revoked":
            logger.warning("License verification failed: revoked key '%s...'", license_key[:8])
            return {"valid": False, "message": "License has been revoked", "token": None}

        expiry_date = datetime.fromisoformat(license_data["expires_at"])
        if datetime.now() > expiry_date:
            license_data["status"] = "expired"
            self._save_licenses()
            logger.warning("License verification failed: expired key '%s...'", license_key[:8])
            return {"valid": False, "message": "License expired", "token": None}

        if license_data["hardware_id"] is None:
            license_data["hardware_id"] = hardware_id
            license_data["activations"] = 1
            self._save_licenses()
            logger.info("License '%s...' bound to hardware ID.", license_key[:8])
        elif license_data["hardware_id"] != hardware_id:
            logger.warning("License verification failed: hardware mismatch for '%s...'", license_key[:8])
            return {"valid": False, "message": "License is bound to another device", "token": None}

        token = self._generate_token(license_key, license_data)
        logger.info("License verified successfully for user '%s'.", license_data["user_id"])
        return {
            "valid": True,
            "message": "License valid",
            "token": token,
            "expires_at": license_data["expires_at"],
            "user_id": license_data["user_id"],
        }

    def _generate_token(self, license_key: str, license_data: Dict[str, Any]) -> str:
        """Generate a JWT token for authenticated sessions."""
        payload = {
            "license_key": license_key,
            "user_id": license_data["user_id"],
            "hardware_id": license_data["hardware_id"],
            "exp": datetime.fromisoformat(license_data["expires_at"]),
            "iat": datetime.now(),
        }

        try:
            return jwt.encode(payload, self.secret_key, algorithm="HS256")
        except Exception as e:
            logger.exception("Failed to generate JWT token: %s", e)
            raise

    def revoke_license(self, license_key: str) -> bool:
        """Revoke a license key."""
        if license_key in self.licenses:
            self.licenses[license_key]["status"] = "revoked"
            self._save_licenses()
            logger.info("License '%s...' revoked successfully.", license_key[:8])
            return True

        logger.warning("License revocation failed: key '%s...' not found.", license_key[:8])
        return False

    def extend_license(self, license_key: str, additional_days: int) -> bool:
        """Extend license duration by the specified number of days."""
        if additional_days <= 0:
            raise ValueError("Extension days must be positive.")

        license_data = self.licenses.get(license_key)
        if not license_data:
            logger.warning("License extension failed: key '%s...' not found.", license_key[:8])
            return False

        current_expiry = datetime.fromisoformat(license_data["expires_at"])
        new_expiry = current_expiry + timedelta(days=additional_days)
        license_data["expires_at"] = new_expiry.isoformat()
        license_data["duration_days"] += additional_days
        self._save_licenses()

        logger.info("License '%s...' extended to %s.", license_key[:8], new_expiry.date())
        return True

    def get_license_info(self, license_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve detailed information for a specific license."""
        license_data = self.licenses.get(license_key)
        return license_data.copy() if license_data else None

    def list_licenses(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all licenses or filter by user ID."""
        licenses = [
            lic.copy() for lic in self.licenses.values()
            if user_id is None or lic["user_id"] == user_id
        ]
        logger.debug("Retrieved %d licenses%s.", len(licenses),
                     f" for user '{user_id}'" if user_id else "")
        return licenses

    def cleanup_expired_licenses(self) -> int:
        """Remove licenses expired for more than 90 days."""
        cleanup_threshold_days = 90
        now = datetime.now()

        expired_keys = [
            key for key, data in self.licenses.items()
            if now > datetime.fromisoformat(data["expires_at"]) + timedelta(days=cleanup_threshold_days)
        ]

        for key in expired_keys:
            del self.licenses[key]

        if expired_keys:
            self._save_licenses()
            logger.info("Cleaned up %d licenses expired >%d days.", len(expired_keys), cleanup_threshold_days)

        return len(expired_keys)


class HardwareIDGenerator:
    """Generate unique hardware identifiers for device binding."""

    @staticmethod
    def get_hardware_id() -> str:
        """Generate a unique hardware ID based on system information."""
        import platform
        import uuid

        system_info = [
            platform.node(),
            platform.machine(),
            platform.processor(),
            str(uuid.getnode())
        ]

        combined = "|".join(system_info)
        hardware_hash = hashlib.sha256(combined.encode()).hexdigest()
        logger.debug("Generated hardware ID from system information.")
        return hardware_hash[:32]


# License creation utility functions
def create_trial_license(server: LicenseServer, user_id: str) -> str:
    """Create a 7-day trial license."""
    return server.generate_license_key(user_id, duration_days=7)


def create_monthly_license(server: LicenseServer, user_id: str) -> str:
    """Create a 30-day license."""
    return server.generate_license_key(user_id, duration_days=30)


def create_yearly_license(server: LicenseServer, user_id: str) -> str:
    """Create a 365-day license."""
    return server.generate_license_key(user_id, duration_days=365)


def create_lifetime_license(server: LicenseServer, user_id: str) -> str:
    """Create a 10-year (lifetime) license."""
    return server.generate_license_key(user_id, duration_days=3650)
