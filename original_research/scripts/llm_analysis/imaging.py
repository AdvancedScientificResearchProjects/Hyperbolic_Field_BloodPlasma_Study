"""Image loading and base64 encoding for LLM vision APIs."""

import base64
import io
import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)

def load_photo_b64(jpg_path: Path) -> str:
    """Load a JPEG photo at original resolution, return base64 string."""
    return base64.b64encode(jpg_path.read_bytes()).decode("ascii")


def build_image_content(b64: str) -> dict:
    """Build a LangChain-compatible image content block."""
    return {
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
    }
