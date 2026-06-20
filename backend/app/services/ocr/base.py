# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class OcrWord:
    text: str
    location: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OcrResult:
    text: str
    words: List[OcrWord] = field(default_factory=list)


class OCRProvider(ABC):
    """OCR 服务抽象基类。"""

    name: str = "base"

    @abstractmethod
    async def recognize(self, image_path: str) -> OcrResult:
        """识别图片中的文字，返回文本内容和位置信息。"""
        pass
