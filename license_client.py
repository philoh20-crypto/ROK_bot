"""
License Client - Handle license validation on client side.
"""

import jwt
import requests
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from license_server import HardwareIDGenerator

logger = logging.getLogger(__name__)


class LicenseClient:
    """Client-side license management and validation."""

    def __init__(self, license_file: str = "license.key"):
        self.license_file = Path(license_file)
        self.license_key: Optional[str] = None
        self.token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.expires_at: Optional[str] = None
        self.hardware_id = HardwareIDGenerator.get_hardware_id()
        self._load_license()

    def _load_license(self):
        """Load license data from local file."""
        if not self.license_file.exists():
            logger.debug("No existing license file found.")
            return

        try:
            with self.license_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            self.license_key = data.get("license_key")
            self.token = data.get("token")
            self.user_id = data.get("user_id")
            self.expires_at = data.get("expires_at")
            logger.info("License data loaded successfully from local file.")
        except json.JSONDecodeError as e:
            logger.error("License file corrupted: %s", e)
        except Exception as e:
            logger.exception("Failed to load license file: %s", e)

    def _save_license(self):
        """Save license data to local file with error handling."""
        try:
            data = {
                "license_key": self.license_key,
                "token": self.token,
                "user_id": self.user_id,
                "expires_at": self.expires_at,
                "hardware_id": self.hardware_id,
                "saved_at": datetime.now().isoformat(),
            }

            with self.license_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("License data saved to local file.")
        except Exception as e:
            logger.exception("Failed to save license file: %s", e)
            raise

    def activate_license(self, license_key: str, server_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Activate license with remote server or local validation.

        Args:
            license_key: License key to activate.
            server_url: Optional URL for remote license server.

        Returns:
            dict: Activation results.
        """
        self.license_key = (license_key or "").strip()

        if not self.license_key:
            return {"success": False, "message": "License key cannot be empty."}

        return self._activate_remote(server_url) if server_url else self._activate_local()

    def _activate_remote(self, server_url: str) -> Dict[str, Any]:
        """Activate license with remote license server."""
        try:
            response = requests.post(
                f"{server_url.rstrip('/')}/activate",
                json={"license_key": self.license_key, "hardware_id": self.hardware_id},
                timeout=15,
            )
            if response.status_code != 200:
                logger.error("License server returned status %d", response.status_code)
                return {"success": False, "message": f"Server error: {response.status_code}"}

            data = response.json()
            if data.get("valid"):
                self.token = data.get("token")
                self.user_id = data.get("user_id")
                self.expires_at = data.get("expires_at")
                self._save_license()
                logger.info("License activated successfully with remote server.")
                return {"success": True, "message": "License activated successfully."}

            error_message = data.get("message", "Unknown error.")
            logger.warning("Remote license activation failed: %s", error_message)
            return {"success": False, "message": error_message}

        except requests.exceptions.Timeout:
            logger.error("License server request timed out.")
            return {"success": False, "message": "Connection to license server timed out."}
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to license server.")
            return {"success": False, "message": "Cannot connect to license server."}
        except requests.exceptions.RequestException as e:
            logger.exception("Network error during license activation: %s", e)
            return {"success": False, "message": f"Network error: {e}"}

    def _activate_local(self) -> Dict[str, Any]:
        """Activate license using local validation (offline/standalone mode)."""
        try:
            from license_server import LicenseServer
            server = LicenseServer()
            result = server.verify_license(self.license_key, self.hardware_id)

            if result["valid"]:
                self.token = result["token"]
                self.user_id = result["user_id"]
                self.expires_at = result["expires_at"]
                self._save_license()
                logger.info("License activated successfully in local mode.")
                return {"success": True, "message": "License activated successfully."}

            error_message = result.get("message", "Validation failed.")
            logger.warning("Local license activation failed: %s", error_message)
            return {"success": False, "message": error_message}

        except ImportError:
            logger.error("Local license server not available.")
            return {"success": False, "message": "Local license server not available."}
        except Exception as e:
            logger.exception("Local license activation error: %s", e)
            return {"success": False, "message": f"Activation error: {e}"}

    def is_valid(self) -> bool:
        """Check if current license is valid and not expired."""
        if not self.token or not self.expires_at:
            logger.debug("License invalid: missing token or expiry date.")
            return False

        try:
            expiry_date = datetime.fromisoformat(self.expires_at)
            if datetime.now() > expiry_date:
                logger.warning("License has expired.")
                return False
            return True
        except ValueError:
            logger.error("Invalid expiry date format in license.")
            return False
        except Exception as e:
            logger.exception("License validation error: %s", e)
            return False

    def get_days_remaining(self) -> int:
        """Get number of days remaining until license expiration."""
        if not self.expires_at:
            return 0
        try:
            expiry_date = datetime.fromisoformat(self.expires_at)
            return max(0, (expiry_date - datetime.now()).days)
        except Exception as e:
            logger.error("Failed to calculate days remaining: %s", e)
            return 0

    def get_license_info(self) -> Dict[str, Any]:
        """Get comprehensive license information."""
        days_remaining = self.get_days_remaining()
        is_valid = self.is_valid()
        license_display = f"{self.license_key[:8]}..." if self.license_key else None
        hardware_display = f"{self.hardware_id[:16]}..." if self.hardware_id else None

        return {
            "user_id": self.user_id,
            "license_key": license_display,
            "expires_at": self.expires_at,
            "days_remaining": days_remaining,
            "is_valid": is_valid,
            "hardware_id": hardware_display,
        }

    def deactivate(self):
        """Deactivate license and remove local license file."""
        self.license_key = None
        self.token = None
        self.user_id = None
        self.expires_at = None

        try:
            if self.license_file.exists():
                self.license_file.unlink()
                logger.info("License file removed during deactivation.")
        except Exception as e:
            logger.exception("Failed to remove license file: %s", e)

        logger.info("License deactivated successfully.")

    def check_and_warn(self) -> bool:
        """
        Check license validity and log appropriate warnings.

        Returns:
            bool: True if license is valid, False otherwise.
        """
        if not self.is_valid():
            logger.error("❌ No valid license found!")
            logger.error("Please activate your license to use the bot.")
            return False

        days_remaining = self.get_days_remaining()
        if days_remaining <= 7:
            logger.warning("⚠️ License expires in %d days!", days_remaining)
            logger.warning("Please renew soon to avoid interruption.")
        elif days_remaining <= 30:
            logger.info("ℹ️ License expires in %d days.", days_remaining)
        else:
            logger.debug("License valid for %d days.", days_remaining)

        return True


class OfflineLicenseValidator:
    """Validate licenses without internet connection using JWT tokens."""

    def __init__(self, secret_key: str):
        self.secret_key = secret_key

    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate JWT token offline with comprehensive error handling."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=["HS256"])
            exp_timestamp = payload.get("exp")

            expiration_date = (
                datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
            )
            if expiration_date and datetime.now() > expiration_date:
                return {"valid": False, "message": "License token has expired."}

            return {
                "valid": True,
                "user_id": payload.get("user_id"),
                "license_key": payload.get("license_key"),
                "hardware_id": payload.get("hardware_id"),
                "expires_at": expiration_date.isoformat() if expiration_date else None,
            }

        except jwt.ExpiredSignatureError:
            return {"valid": False, "message": "License token signature has expired."}
        except jwt.InvalidTokenError as e:
            return {"valid": False, "message": f"Invalid license token: {e}"}
        except Exception as e:
            return {"valid": False, "message": f"Token validation error: {e}"}


def display_license_banner(client: LicenseClient):
    """Display formatted license information banner."""
    info = client.get_license_info()
    print("\n" + "=" * 60)
    print("LICENSE INFORMATION")
    print("=" * 60)
    print(f"User ID:        {info['user_id']}")
    print(f"License Key:    {info['license_key']}")
    print(f"Expiration:     {info['expires_at']}")
    print(f"Days Remaining: {info['days_remaining']}")
    print(f"Status:         {'✓ ACTIVE' if info['is_valid'] else '✗ INACTIVE'}")
    print("=" * 60 + "\n")

