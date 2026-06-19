# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class OCRProvider(ABC):
    """OCR 服务抽象基类。"""

    name: str = "base"

    @abstractmethod
    async def recognize(self, image_path: str) -> str:
        """识别图片中的文字，返回文本内容。"""
        pass
