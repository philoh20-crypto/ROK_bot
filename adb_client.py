"""
ADB Client - Pure Python ADB wrapper for BlueStacks communication
"""

import io
import time
import logging
from typing import Optional, Tuple, List

from ppadb.client import Client as AdbClient
from ppadb.device import Device
from PIL import Image

logger = logging.getLogger(__name__)


class RoKADBClient:
    """Handles ADB connection and communication with BlueStacks."""

    def __init__(self, host: str = "127.0.0.1", port: int = 5037):
        self.host = host
        self.port = port
        self.client: Optional[AdbClient] = None
        self.device: Optional[Device] = None
        self.package_name = "com.lilithgames.roc.gp"  # Rise of Kingdoms package

    # --------------------------------------------------------------------------
    # Connection Methods
    # --------------------------------------------------------------------------

    def connect(self) -> bool:
        """Connect to the ADB server."""
        try:
            self.client = AdbClient(host=self.host, port=self.port)
            logger.info(f"Connected to ADB server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.exception(f"Failed to connect to ADB server: {e}")
            return False

    def get_devices(self) -> List[Device]:
        """Return list of connected ADB devices."""
        if not self.client:
            logger.warning("ADB client not initialized; call connect() first.")
            return []
        return self.client.devices()

    def select_device(self, serial: Optional[str] = None) -> bool:
        """Select a specific device by serial, or the first one if none is given."""
        devices = self.get_devices()
        if not devices:
            logger.error("No ADB devices found.")
            return False

        if serial:
            device = next((d for d in devices if d.serial == serial), None)
            if not device:
                logger.error(f"Device with serial '{serial}' not found.")
                return False
            self.device = device
            logger.info(f"Selected device: {serial}")
        else:
            self.device = devices[0]
            logger.info(f"Auto-selected device: {self.device.serial}")
        return True

    def is_connected(self) -> bool:
        """Check if the selected device is connected and responsive."""
        if not self.device:
            logger.debug("No device connected.")
            return False
        try:
            self.device.get_state()
            return True
        except Exception as e:
            logger.warning(f"Device unresponsive: {e}")
            return False

    # --------------------------------------------------------------------------
    # Input Controls
    # --------------------------------------------------------------------------

    def tap(self, x: int, y: int, duration_ms: int = 100) -> bool:
        """Tap at the given coordinates for a short duration."""
        if not self.device:
            logger.error("No device connected for tap operation.")
            return False
        try:
            self.device.shell(f"input tap {x} {y}")
            time.sleep(duration_ms / 1000.0)
            logger.debug(f"Tapped at ({x}, {y}) for {duration_ms} ms.")
            return True
        except Exception as e:
            logger.error(f"Tap operation failed at ({x}, {y}): {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 500) -> bool:
        """Swipe from (x1, y1) to (x2, y2) with a specified duration."""
        if not self.device:
            logger.error("No device connected for swipe operation.")
            return False
        try:
            self.device.shell(f"input swipe {x1} {y1} {x2} {y2} {duration_ms}")
            logger.debug(f"Swiped from ({x1}, {y1}) to ({x2}, {y2}) in {duration_ms} ms.")
            return True
        except Exception as e:
            logger.error(f"Swipe operation failed: {e}")
            return False

    def input_text(self, text: str) -> bool:
        """Input text on the device (e.g., for chat or naming)."""
        if not self.device:
            logger.error("No device connected for text input.")
            return False
        try:
            # Escape special characters safely for shell input
            escaped_text = text.replace(" ", "%s").replace("'", "\\'")
            self.device.shell(f"input text '{escaped_text}'")
            logger.debug(f"Input text: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to input text: {e}")
            return False

    def press_back(self) -> bool:
        """Simulate pressing the back button."""
        return self._press_key("KEYCODE_BACK", "back")

    def press_home(self) -> bool:
        """Simulate pressing the home button."""
        return self._press_key("KEYCODE_HOME", "home")

    def _press_key(self, keycode: str, name: str) -> bool:
        """Generic helper for key events."""
        if not self.device:
            logger.error(f"No device connected to press {name} button.")
            return False
        try:
            self.device.shell(f"input keyevent {keycode}")
            logger.debug(f"Pressed {name} button.")
            return True
        except Exception as e:
            logger.error(f"Failed to press {name} button: {e}")
            return False

    # --------------------------------------------------------------------------
    # Device Info & Screen Operations
    # --------------------------------------------------------------------------

    def get_screenshot(self) -> Optional[Image.Image]:
        """Capture and return a screenshot from the device."""
        if not self.device:
            logger.error("No device connected for screenshot capture.")
            return None
        try:
            screenshot_bytes = self.device.screencap()
            if not screenshot_bytes:
                logger.warning("Screenshot returned empty bytes.")
                return None
            image = Image.open(io.BytesIO(screenshot_bytes))
            logger.debug("Screenshot captured successfully.")
            return image
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return None

    def get_screen_resolution(self) -> Tuple[int, int]:
        """Retrieve the device screen resolution (width, height)."""
        default_res = (1920, 1080)
        if not self.device:
            logger.warning("No device connected; returning default resolution.")
            return default_res

        try:
            output = self.device.shell("wm size")
            if "Physical size:" in output:
                size_str = output.split("Physical size:")[1].strip()
                width, height = map(int, size_str.split("x"))
                logger.debug(f"Detected screen resolution: {width}x{height}")
                return width, height
            logger.warning("Unexpected output from 'wm size' command.")
        except Exception as e:
            logger.error(f"Failed to get screen resolution: {e}")
        return default_res

    # --------------------------------------------------------------------------
    # App Management
    # --------------------------------------------------------------------------

    def start_app(self) -> bool:
        """Launch Rise of Kingdoms on the device."""
        if not self.device:
            logger.error("No device connected to start app.")
            return False
        try:
            self.device.shell(f"monkey -p {self.package_name} -c android.intent.category.LAUNCHER 1")
            logger.info("Launching Rise of Kingdoms...")
            time.sleep(5)  # Wait for the app to start
            return True
        except Exception as e:
            logger.error(f"Failed to start Rise of Kingdoms: {e}")
            return False

    def stop_app(self) -> bool:
        """Force-stop Rise of Kingdoms."""
        if not self.device:
            logger.error("No device connected to stop app.")
            return False
        try:
            self.device.shell(f"am force-stop {self.package_name}")
            logger.info("Stopped Rise of Kingdoms.")
            return True
        except Exception as e:
            logger.error(f"Failed to stop Rise of Kingdoms: {e}")
            return False

    def is_app_running(self) -> bool:
        """Check if Rise of Kingdoms is currently running."""
        if not self.device:
            logger.debug("No device connected for app status check.")
            return False
        try:
            output = self.device.shell(f"pidof {self.package_name}")
            is_running = bool(output.strip())
            logger.debug(f"App running check: {is_running}")
            return is_running
        except Exception as e:
            logger.error(f"Failed to check app running status: {e}")
            return False

    # --------------------------------------------------------------------------
    # Cleanup
    # --------------------------------------------------------------------------

    def disconnect(self):
        """Disconnect from device and clean up resources."""
        self.device = None
        self.client = None
        logger.info("Disconnected from ADB.")
