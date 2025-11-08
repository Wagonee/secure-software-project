import uuid
from pathlib import Path
from typing import Optional, Tuple

MAX_BYTES = 5_000_000
ALLOWED = {"image/png", "image/jpeg"}

PNG = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


def sniff_image_type(data: bytes) -> Optional[str]:
    if data.startswith(PNG):
        return "image/png"
    if data.startswith(JPEG_SOI) and data.endswith(JPEG_EOI):
        return "image/jpeg"
    return None


def secure_save(base_dir: str, filename_hint: str, data: bytes) -> Tuple[bool, str]:
    if len(data) > MAX_BYTES:
        return False, "too_big"
    mt = sniff_image_type(data)
    if mt not in ALLOWED:
        return False, "bad_type"
    root = Path(base_dir).resolve()
    ext = ".png" if mt == "image/png" else ".jpg"
    name = f"{uuid.uuid4()}{ext}"
    path = (root / name).resolve()
    if not str(path).startswith(str(root)):
        return False, "path_traversal"
    if any(p.is_symlink() for p in path.parents):
        return False, "symlink_parent"
    root.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    return True, str(path)
