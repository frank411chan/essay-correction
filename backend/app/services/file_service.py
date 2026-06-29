import base64
import io
import uuid
from pathlib import Path
from PIL import Image
from fastapi import UploadFile, HTTPException

from app.config import get_settings, PROJECT_ROOT

settings = get_settings()
UPLOAD_DIR = settings.upload_dir_path
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_IMAGE_DIMENSION = 2048  # 手写文字识别需要较高分辨率
JPEG_QUALITY = 95  # 手写文字需要更高质量，避免模糊
MAX_UPLOAD_FILES = 3


def validate_image(file: UploadFile) -> str:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，仅支持 {', '.join(ALLOWED_EXTENSIONS)}",
        )
    return ext


def compress_image(content: bytes, max_size: tuple = (MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), quality: int = JPEG_QUALITY) -> bytes:
    """压缩图片，控制大小和分辨率。"""
    try:
        img = Image.open(io.BytesIO(content))
        # 转换模式以兼容 JPEG
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # 等比缩放，保持较高分辨率以识别手写文字
        img.thumbnail(max_size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        img.save(output, format="JPEG", quality=quality, optimize=True)
        return output.getvalue()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"图片处理失败: {str(e)}")


def save_upload_file(file: UploadFile) -> str:
    validate_image(file)

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 10MB")

    # 压缩图片
    compressed = compress_image(content)

    ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / filename

    with open(file_path, "wb") as f:
        f.write(compressed)

    # 返回相对于项目根目录的路径
    return str(file_path.relative_to(PROJECT_ROOT))


def save_upload_files(files: list[UploadFile]) -> list[str]:
    """保存多张上传图片，返回路径列表。"""
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail=f"一次最多上传 {MAX_UPLOAD_FILES} 张图片")

    paths = []
    for file in files:
        paths.append(save_upload_file(file))
    return paths


def image_to_base64(file_path: str) -> str:
    # 如果传入相对路径，先转为绝对路径
    path = PROJECT_ROOT / file_path if not Path(file_path).is_absolute() else Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"图片不存在: {file_path}")

    with open(path, "rb") as f:
        content = f.read()

    encoded = base64.b64encode(content).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def get_image_path(file_path: str) -> Path:
    return PROJECT_ROOT / file_path if not Path(file_path).is_absolute() else Path(file_path)
