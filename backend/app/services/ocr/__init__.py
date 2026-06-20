# -*- coding: utf-8 -*-
from app.services.ocr.base import OCRProvider, OcrResult, OcrWord
from app.services.ocr.kimi_ocr import KimiOCRProvider
from app.services.ocr.baidu_ocr import BaiduOCRProvider
from app.services.ocr.tencent_ocr import TencentOCRProvider


OCR_ENGINES = {
    "kimi": KimiOCRProvider,
    "baidu": BaiduOCRProvider,
    "tencent": TencentOCRProvider,
}


def get_ocr_provider(engine: str) -> OCRProvider:
    if engine not in OCR_ENGINES:
        raise ValueError(f"不支持的 OCR 引擎: {engine}，可用: {list(OCR_ENGINES.keys())}")
    return OCR_ENGINES[engine]()
