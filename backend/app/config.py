from pathlib import Path
from pydantic_settings import BaseSettings
from functools import lru_cache


# 项目根目录：backend 的上级目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    moonshot_api_key: str
    moonshot_base_url: str = "https://api.moonshot.cn/v1"
    moonshot_model: str = "moonshot-v1-32k-vision-preview"

    database_url: str = "sqlite:///./essay_correction.db"
    upload_dir: str = "./uploads"

    host: str = "0.0.0.0"
    port: int = 8000

    # OCR 配置
    baidu_ocr_app_id: str = ""
    baidu_ocr_api_key: str = ""
    baidu_ocr_secret_key: str = ""

    tencent_ocr_secret_id: str = ""
    tencent_ocr_secret_key: str = ""

    # 批量扫描目录
    batch_scan_dir: str = "/mnt/hgfs/vm_share/workspace/essay-correction"

    # 定时扫描配置
    auto_scan_enabled: bool = True
    auto_scan_time: str = "22:00"  # 每天 22:00 自动扫描当天目录

    @property
    def upload_dir_path(self) -> Path:
        return PROJECT_ROOT / self.upload_dir

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
