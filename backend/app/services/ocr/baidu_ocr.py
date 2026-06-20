# -*- coding: utf-8 -*-
import base64
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import get_settings
from app.services.ocr.base import OCRProvider, OcrResult, OcrWord


class BaiduOCRProvider(OCRProvider):
    name = "baidu"

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.baidu_ocr_app_id
        self.api_key = settings.baidu_ocr_api_key
        self.secret_key = settings.baidu_ocr_secret_key
        self.access_token = None

    def _get_access_token(self) -> str:
        if self.access_token:
            return self.access_token

        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.api_key,
            "client_secret": self.secret_key,
        }

        req = Request(url, data=urlencode(params).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))

        self.access_token = result["access_token"]
        return self.access_token

    async def recognize(self, image_path: str) -> OcrResult:
        if not self.api_key or not self.secret_key:
            raise ValueError("百度 OCR 未配置 API Key 和 Secret Key")

        access_token = self._get_access_token()
        url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting?access_token={access_token}"

        with open(Path(image_path), "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        params = {"image": image_data}
        req = Request(url, data=urlencode(params).encode("utf-8"), method="POST")
        req.add_header("Content-Type", "application/x-www-form-urlencoded")

        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        if "error_code" in result:
            raise RuntimeError(f"百度 OCR 错误: {result.get('error_msg')}")

        words_result = result.get("words_result", [])
        words = []
        text_lines = []

        for item in words_result:
            word_text = item.get("words", "").strip()
            if not word_text:
                continue
            location = item.get("location", {})
            words.append(OcrWord(text=word_text, location=location))
            text_lines.append(word_text)

        # 手写识别按行返回，这里用换行拼接
        return OcrResult(text="\n".join(text_lines), words=words)
