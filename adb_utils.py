"""
ADB Utilities - Image processing and template matching for game automation
"""
import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """Handle image processing and template matching operations."""

    # ===================== Image Conversions =====================
    @staticmethod
    def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
        """Convert a PIL Image (RGB) to an OpenCV image (BGR)."""
        return cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    @staticmethod
    def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
        """Convert an OpenCV image (BGR) to a PIL Image (RGB)."""
        return Image.fromarray(cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB))

    # ===================== Template Matching =====================
    @staticmethod
    def find_template(
        screenshot: Image.Image,
        template_path: str,
        threshold: float = 0.8,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> Optional[Tuple[int, int, int, int]]:
        """
        Find a single instance of a template in the screenshot.

        Args:
            screenshot: PIL Image to search within.
            template_path: Path to the template image file.
            threshold: Confidence threshold (0–1).
            method: OpenCV template matching method.

        Returns:
            (x, y, width, height) if found, else None.
        """
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                logger.error(f"Unable to load template: {template_path}")
                return None

            img = ImageProcessor.pil_to_cv2(screenshot)
            result = cv2.matchTemplate(img, template, method)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                h, w = template.shape[:2]
                logger.debug(f"Template found at ({max_loc[0]}, {max_loc[1]}) with confidence {max_val:.3f}")
                return max_loc[0], max_loc[1], w, h

            logger.debug(f"Template not found (best confidence: {max_val:.3f})")
            return None

        except Exception as e:
            logger.exception(f"Template matching failed for '{template_path}': {e}")
            return None

    @staticmethod
    def find_all_templates(
        screenshot: Image.Image,
        template_path: str,
        threshold: float = 0.8,
        method: int = cv2.TM_CCOEFF_NORMED
    ) -> List[Tuple[int, int, int, int]]:
        """Find all instances of a template in a screenshot above the threshold."""
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                logger.error(f"Template not found: {template_path}")
                return []

            img = ImageProcessor.pil_to_cv2(screenshot)
            result = cv2.matchTemplate(img, template, method)

            h, w = template.shape[:2]
            y_locs, x_locs = np.where(result >= threshold)
            boxes = [(x, y, w, h) for x, y in zip(x_locs, y_locs)]

            filtered = ImageProcessor._non_max_suppression(boxes)
            logger.debug(f"Found {len(filtered)} template instances (raw: {len(boxes)})")
            return filtered

        except Exception as e:
            logger.exception(f"Multi-template matching failed: {e}")
            return []

    # ===================== Utility Methods =====================
    @staticmethod
    def _non_max_suppression(
        boxes: List[Tuple[int, int, int, int]],
        overlap_threshold: float = 0.3
    ) -> List[Tuple[int, int, int, int]]:
        """Apply non-maximum suppression to remove overlapping bounding boxes."""
        if not boxes:
            return []

        boxes_array = np.array(boxes)
        x1, y1 = boxes_array[:, 0], boxes_array[:, 1]
        x2, y2 = x1 + boxes_array[:, 2], y1 + boxes_array[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        indices = np.argsort(y2)
        selected = []

        while indices.size > 0:
            i = indices[-1]
            selected.append(i)
            if indices.size == 1:
                break

            remaining = indices[:-1]
            xx1 = np.maximum(x1[i], x1[remaining])
            yy1 = np.maximum(y1[i], y1[remaining])
            xx2 = np.minimum(x2[i], x2[remaining])
            yy2 = np.minimum(y2[i], y2[remaining])

            inter_w = np.maximum(0, xx2 - xx1 + 1)
            inter_h = np.maximum(0, yy2 - yy1 + 1)
            inter_area = inter_w * inter_h

            union_area = areas[i] + areas[remaining] - inter_area
            overlap = inter_area / union_area

            indices = remaining[overlap <= overlap_threshold]

        return [tuple(boxes_array[i]) for i in selected]

    @staticmethod
    def find_color(
        screenshot: Image.Image,
        color_rgb: Tuple[int, int, int],
        tolerance: int = 10
    ) -> List[Tuple[int, int]]:
        """Find all pixels matching a specific RGB color within a given tolerance."""
        try:
            img = cv2.cvtColor(ImageProcessor.pil_to_cv2(screenshot), cv2.COLOR_BGR2RGB)

            lower = np.maximum(0, np.array(color_rgb) - tolerance)
            upper = np.minimum(255, np.array(color_rgb) + tolerance)

            mask = cv2.inRange(img, lower, upper)
            coords = cv2.findNonZero(mask)

            if coords is not None:
                points = [(int(pt[0][0]), int(pt[0][1])) for pt in coords]
                logger.debug(f"Found {len(points)} pixels matching color {color_rgb}")
                return points
            return []

        except Exception as e:
            logger.exception(f"Color detection failed: {e}")
            return []

    @staticmethod
    def crop_region(screenshot: Image.Image, x: int, y: int, width: int, height: int) -> Image.Image:
        """Crop a rectangular region from the screenshot."""
        return screenshot.crop((x, y, x + width, y + height))

    @staticmethod
    def compare_images(img1: Image.Image, img2: Image.Image) -> float:
        """
        Compare two images using structural similarity (SSIM).
        Returns a similarity score between 0 and 1.
        """
        try:
            img1_gray = np.array(img1.convert('L'))
            img2_gray = np.array(img2.convert('L'))

            if img1_gray.shape != img2_gray.shape:
                img2_gray = cv2.resize(img2_gray, (img1_gray.shape[1], img1_gray.shape[0]))

            from skimage.metrics import structural_similarity as ssim
            score, _ = ssim(img1_gray, img2_gray, full=True)
            return float(np.clip(score, 0.0, 1.0))

        except ImportError:
            logger.warning("scikit-image not installed, falling back to correlation method")
            size = (100, 100)
            arr1 = np.array(img1.resize(size)).astype(float).flatten()
            arr2 = np.array(img2.resize(size)).astype(float).flatten()
            corr = np.corrcoef(arr1, arr2)[0, 1]
            return max(0.0, corr if not np.isnan(corr) else 0.0)

        except Exception as e:
            logger.exception(f"Image comparison failed: {e}")
            return 0.0

    @staticmethod
    def extract_text_region(
        screenshot: Image.Image,
        x: int, y: int, width: int, height: int
    ) -> str:
        """Extract text from a region using OCR (pytesseract required)."""
        try:
            import pytesseract

            region = ImageProcessor.crop_region(screenshot, x, y, width, height)
            region_cv = ImageProcessor.pil_to_cv2(region)
            gray = cv2.cvtColor(region_cv, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            text = pytesseract.image_to_string(thresh).strip()
            if text:
                logger.debug(f"OCR extracted text: '{text}'")
            return text

        except ImportError:
            logger.warning("pytesseract not available for OCR text extraction")
            return ""

        except Exception as e:
            logger.exception(f"Text extraction failed: {e}")
            return ""


class CoordinateMapper:
    """Handle coordinate mapping between different screen resolutions."""

    def __init__(self, base_width: int = 1920, base_height: int = 1080):
        self.base_width = base_width
        self.base_height = base_height
        self.current_width = base_width
        self.current_height = base_height

    def set_current_resolution(self, width: int, height: int):
        """Set the current screen resolution for scaling."""
        self.current_width, self.current_height = width, height
        logger.debug(f"Resolution set: {width}x{height}")

    def scale_coordinates(self, x: int, y: int) -> Tuple[int, int]:
        """Scale coordinates from base resolution to current resolution."""
        sx, sy = self.get_scale_factors()
        return int(round(x * sx)), int(round(y * sy))

    def scale_region(self, x: int, y: int, width: int, height: int) -> Tuple[int, int, int, int]:
        """Scale a rectangular region from base resolution to current resolution."""
        sx, sy = self.get_scale_factors()
        return (
            int(round(x * sx)),
            int(round(y * sy)),
            int(round(width * sx)),
            int(round(height * sy)),
        )

    def get_scale_factors(self) -> Tuple[float, float]:
        """Return current scaling factors (width, height)."""
        return self.current_width / self.base_width, self.current_height / self.base_height
