# -*- coding: utf-8 -*-
from openai import OpenAI

from app.config import get_settings
from app.services.ocr.base import OCRProvider
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

    async def recognize(self, image_path: str) -> str:
        image_base64 = image_to_base64(image_path)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个OCR文字识别助手，只识别图片中实际存在的文字，不要添加、推测或补充图片中没有的内容。",
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "请识别图片中的文字，只返回识别出的文字内容，不要添加任何解释、总结或额外内容。",
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_base64},
                        },
                    ],
                },
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        text = response.choices[0].message.content.strip()
        # 去除可能的 markdown 代码块标记
        if text.startswith("```"):
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()
        return text
