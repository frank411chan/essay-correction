# -*- coding: utf-8 -*-
import asyncio
import base64
import json
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.config import get_settings
from app.services.ocr.base import OCRProvider, OcrResult, OcrWord


class BaiduOCRProvider(OCRProvider):
    """百度手写作文（多模态）OCR 提供者。

    使用异步接口：先调用 create_task 提交任务，再通过 get_result 轮询结果。
    文档：https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting_composition
    """

    name = "baidu"

    CREATE_TASK_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting_composition/create_task"
    GET_RESULT_URL = "https://aip.baidubce.com/rest/2.0/ocr/v1/handwriting_composition/get_result"

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

        if "access_token" not in result:
            raise RuntimeError(f"获取百度 access_token 失败: {result}")

        self.access_token = result["access_token"]
        return self.access_token

    def _post_json(self, url: str, params: dict, timeout: int = 60) -> dict:
        """发送 JSON POST 请求。"""
        data = json.dumps(params, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")

        with urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _create_task(self, image_path: str) -> str:
        """提交识别任务，返回 task_id。"""
        access_token = self._get_access_token()
        url = f"{self.CREATE_TASK_URL}?access_token={access_token}"

        with open(Path(image_path), "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        # 使用字级粒度，便于后续原图批注
        params = {
            "image": image_data,
            "recognize_granularity": "word",
        }

        result = self._post_json(url, params, timeout=30)

        if result.get("error_code"):
            raise RuntimeError(f"百度 OCR 提交任务失败: {result.get('error_msg')} (code={result.get('error_code')})")

        task_id = result.get("result", {}).get("task_id")
        if not task_id:
            raise RuntimeError(f"百度 OCR 未返回 task_id: {result}")

        return task_id

    def _get_result(self, task_id: str) -> dict:
        """轮询获取识别结果。"""
        access_token = self._get_access_token()
        url = f"{self.GET_RESULT_URL}?access_token={access_token}"

        # 文档建议提交后 5~10 秒开始轮询
        time.sleep(6)

        max_retries = 30
        interval = 3
        for attempt in range(max_retries):
            result = self._post_json(url, {"task_id": task_id}, timeout=30)

            if result.get("error_code"):
                raise RuntimeError(f"百度 OCR 获取结果失败: {result.get('error_msg')} (code={result.get('error_code')})")

            task_result = result.get("result", {})
            status = task_result.get("status", "").lower()

            if status == "success":
                return task_result
            elif status in ("failed", "failure"):
                raise RuntimeError(f"百度 OCR 任务执行失败: {task_result}")

            # pending / processing，继续等待
            time.sleep(interval)

        raise RuntimeError("百度 OCR 获取结果超时")

    @staticmethod
    def _extract_words(content_data: dict) -> List[OcrWord]:
        """从 content.lines/chars 中提取字级位置信息。

        注意：实际接口返回 lines 为 list[list[dict]]，每个内层列表通常含一个 line dict。
        """
        words = []
        lines = content_data.get("lines", []) or []
        for line in lines:
            # 兼容 list[dict] 和 dict 两种形式
            if isinstance(line, list) and line:
                line = line[0]
            if not isinstance(line, dict):
                continue

            chars = line.get("chars", []) or []
            for char_info in chars:
                if isinstance(char_info, list) and char_info:
                    char_info = char_info[0]
                if not isinstance(char_info, dict):
                    continue
                char_text = char_info.get("char", "").strip()
                if not char_text:
                    continue
                bbox = char_info.get("bbox", {})
                words.append(OcrWord(text=char_text, location=bbox))
        return words

    @staticmethod
    def _extract_text(ocr_result: dict) -> str:
        """提取作文文本，优先使用 essayOverall.contentText。"""
        essay_overall = ocr_result.get("essayOverall", {})
        title_text = essay_overall.get("titleText", "")
        content_text = essay_overall.get("contentText", "")

        parts = []
        if title_text:
            parts.append(title_text)
        if content_text:
            parts.append(content_text)

        return "\n".join(parts)

    async def recognize(self, image_path: str) -> OcrResult:
        if not self.api_key or not self.secret_key:
            raise ValueError("百度 OCR 未配置 API Key 和 Secret Key")

        # 在事件循环中运行同步的 HTTP 请求，避免阻塞
        loop = asyncio.get_event_loop()
        task_id = await loop.run_in_executor(None, self._create_task, image_path)
        task_result = await loop.run_in_executor(None, self._get_result, task_id)

        ocr_result = task_result.get("result", {})
        text = self._extract_text(ocr_result)
        words = self._extract_words(ocr_result.get("content", {}))

        return OcrResult(text=text, words=words)

    async def recognize_multiple(self, image_paths: List[str]) -> OcrResult:
        """多图识别：依次提交任务并轮询，按顺序拼接文本。

        由于 create_task QPS 限制为 2，任务提交之间间隔 0.6 秒。
        """
        if not image_paths:
            return OcrResult(text="", words=[])

        texts = []
        words = []

        for idx, path in enumerate(image_paths):
            if idx > 0:
                await asyncio.sleep(0.6)
            result = await self.recognize(path)
            texts.append(result.text)
            words.extend(result.words)

        return OcrResult(text="\n".join(texts), words=words)
