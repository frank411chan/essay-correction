# -*- coding: utf-8 -*-
from openai import OpenAI

from app.config import get_settings
from app.services.ocr.base import OCRProvider, OcrResult
from app.services.file_service import image_to_base64


class KimiOCRProvider(OCRProvider):
    name = "kimi"

    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.moonshot_api_key,
            base_url=settings.moonshot_base_url,
        )
        self.model = settings.moonshot_model

    def _call_llm(self, messages, max_tokens=8192, temperature=0.05):
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content.strip()

    def _extract_text(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            raw = "\n".join(lines).strip()
        return raw

    def _proofread_text(self, draft_text: str, image_base64: str) -> str:
        """二次校对：让模型对照图片修正初稿中的识别错误。"""
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位严谨的手写作文校对专家。你的任务是：根据原始图片，检查并修正已识别出的作文文本。\n"
                    "要求：\n"
                    "1. 必须逐字逐句对照图片，确保不遗漏任何文字。\n"
                    "2. 只修正你100%确定的识别错误（错字、漏字、多字、被误识别的字），不确定的字必须保留初稿原样。\n"
                    "3. 保持原文的段落结构、换行和标点不变，禁止合并段落。\n"
                    "4. 不要自动修改学生的错别字或病句，要忠实还原学生写下的内容。\n"
                    "5. 只输出校对后的作文纯文本，不要解释、总结或 markdown 代码块。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"以下是初稿识别结果，请对照图片逐字校对，输出最忠实原稿的完整文本：\n\n{draft_text}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_base64},
                    },
                ],
            },
        ]
        proofread = self._call_llm(messages, max_tokens=8192, temperature=0.05)
        return self._extract_text(proofread)

    async def recognize(self, image_path: str) -> OcrResult:
        image_base64 = image_to_base64(image_path)

        # 第一步：初稿识别
        draft_messages = [
            {
                "role": "system",
                "content": (
                    "你是一位专注于手写作文图片的OCR识别专家。任务要求：\n"
                    "1. 必须识别图片中的全部文字，严禁遗漏、省略、概括或总结。\n"
                    "2. 严禁添加、推测或补充图片中没有的内容。\n"
                    "3. 必须保持作文原有的段落结构、换行和标点，不要合并段落。\n"
                    "4. 对手写汉字要逐字仔细辨认，笔画相近的字（如：未/末、己/已/巳、人/入、风/凤、拨/拔等）要结合上下文判断。\n"
                    "5. 优先保证文字忠实原稿，不要自动修正错别字或病句。\n"
                    "6. 图片中的标题、题号、提示文字等也应一并识别。\n"
                    "7. 只输出识别到的纯文本，不要解释、总结、markdown代码块或任何额外内容。"
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "请准确识别这张学生作文图片中的全部文字，按原稿格式输出，不要遗漏任何内容。",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_base64},
                    },
                ],
            },
        ]
        draft = self._extract_text(self._call_llm(draft_messages, max_tokens=8192, temperature=0.05))

        # 第二步：对照图片校对，提升准确率
        proofread = self._proofread_text(draft, image_base64)

        # Kimi 不提供位置信息
        return OcrResult(text=proofread, words=[])

