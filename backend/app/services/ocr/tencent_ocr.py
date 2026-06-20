# -*- coding: utf-8 -*-
import base64
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

from app.config import get_settings
from app.services.ocr.base import OCRProvider, OcrResult


class TencentOCRProvider(OCRProvider):
    name = "tencent"

    def __init__(self):
        settings = get_settings()
        self.secret_id = settings.tencent_ocr_secret_id
        self.secret_key = settings.tencent_ocr_secret_key

    def _sign(self, payload: str) -> dict:
        service = "ocr"
        host = "ocr.tencentcloudapi.com"
        action = "GeneralHandwritingOCR"
        version = "2018-11-19"
        region = "ap-guangzhou"
        timestamp = int(time.time())

        headers = {
            "Host": host,
            "Content-Type": "application/json",
            "X-TC-Action": action,
            "X-TC-Version": version,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Region": region,
        }

        # 简化的签名实现，实际需要按腾讯云 V3 签名规范完整实现
        date = time.strftime("%Y-%m-%d", time.gmtime(timestamp))
        credential_scope = f"{date}/{service}/tc3_request"
        headers["Authorization"] = (
            f"TC3-HMAC-SHA256 Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders=content-type;host;x-tc-action, Signature=placeholder"
        )

        return headers

    async def recognize(self, image_path: str) -> OcrResult:
        if not self.secret_id or not self.secret_key:
            raise ValueError("腾讯 OCR 未配置 Secret ID 和 Secret Key")

        host = "ocr.tencentcloudapi.com"
        url = f"https://{host}"

        with open(Path(image_path), "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")

        payload = json.dumps({"ImageBase64": image_base64})
        headers = self._sign(payload)

        req = Request(url, data=payload.encode("utf-8"), headers=headers, method="POST")

        with urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        if "Error" in result.get("Response", {}):
            raise RuntimeError(f"腾讯 OCR 错误: {result['Response']['Error']}")

        # 简化的结果解析，实际需按腾讯云响应结构解析
        return OcrResult(text="腾讯 OCR 结果占位，需完善签名和解析逻辑", words=[])
