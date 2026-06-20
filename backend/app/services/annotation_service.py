# -*- coding: utf-8 -*-
"""生成带批注高亮的作文图片。"""
import io
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.config import PROJECT_ROOT


def _get_font(size: int):
    """获取中文字体。"""
    font_paths = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/arphic/uming.ttc",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _generate_colors(n: int) -> list:
    """生成区分度高的颜色。"""
    colors = [
        (255, 0, 0),      # 红
        (0, 128, 0),      # 绿
        (0, 0, 255),      # 蓝
        (255, 165, 0),    # 橙
        (128, 0, 128),    # 紫
        (255, 192, 0),    # 金黄
        (220, 20, 60),    # 深红
        (0, 128, 128),    # 青
    ]
    return [colors[i % len(colors)] for i in range(n)]


def _match_words_to_paragraph(words: list, paragraph_text: str) -> list:
    """根据段落文本匹配 OCR 单词位置。

    简单策略：
    1. 对 paragraph_text 按行/句拆分
    2. 在 words 中顺序查找包含这些关键词的 word
    3. 返回匹配到的 word 位置列表
    """
    if not words or not paragraph_text:
        return []

    # 提取段落中的关键词（长度 >= 2 的字符片段）
    keywords = []
    for i in range(len(paragraph_text) - 1):
        keyword = paragraph_text[i:i + 2]
        if keyword.strip():
            keywords.append(keyword)
    if not keywords:
        return []

    matched = []
    used_indices = set()

    for keyword in keywords[:5]:  # 每个段落最多匹配 5 个位置
        for idx, word_info in enumerate(words):
            if idx in used_indices:
                continue
            word_text = word_info.get("text", "")
            if keyword in word_text:
                loc = word_info.get("location", {})
                if loc:
                    matched.append(loc)
                    used_indices.add(idx)
                    break

    return matched


def generate_annotated_image(essay) -> bytes:
    """在作文原图上绘制段落批注高亮框。"""
    image_path = PROJECT_ROOT / essay.image_path
    if not image_path.exists():
        raise FileNotFoundError(f"图片不存在: {essay.image_path}")

    img = Image.open(image_path)
    if img.mode != "RGB":
        img = img.convert("RGB")

    draw = ImageDraw.Draw(img)
    ocr_words = essay.ocr_words or []
    paragraph_comments = essay.paragraph_comments or []

    colors = _generate_colors(len(paragraph_comments))

    for idx, comment_item in enumerate(paragraph_comments):
        comment = comment_item.get("comment", "")
        paragraph_index = comment_item.get("paragraph_index", idx + 1)
        color = colors[idx]

        # 在段落文本中找一些关键词来匹配位置
        # 简单做法：用 recognized_text 按段落拆分后取对应段落文本
        paragraph_text = ""
        if essay.recognized_text:
            paragraphs = [p.strip() for p in essay.recognized_text.split("\n") if p.strip()]
            if 1 <= paragraph_index <= len(paragraphs):
                paragraph_text = paragraphs[paragraph_index - 1]

        # 如果段落文本为空，尝试用 comment 关键词匹配
        if not paragraph_text:
            paragraph_text = comment[:20]

        matched_locations = _match_words_to_paragraph(ocr_words, paragraph_text)

        # 绘制匹配到的位置框
        for loc in matched_locations:
            left = loc.get("left", 0)
            top = loc.get("top", 0)
            width = loc.get("width", 0)
            height = loc.get("height", 0)

            if width <= 0 or height <= 0:
                continue

            # 画粗边框
            for thickness in range(3):
                draw.rectangle(
                    [left - thickness, top - thickness, left + width + thickness, top + height + thickness],
                    outline=color,
                )

        # 在图片边缘绘制批注编号和简短评语
        if matched_locations:
            first_loc = matched_locations[0]
            label_x = first_loc.get("left", 10)
            label_y = max(first_loc.get("top", 10) - 25, 5)
            label = f"[{idx + 1}]"

            try:
                font = _get_font(20)
            except Exception:
                font = ImageFont.load_default()

            # 画小圆角背景
            bbox = draw.textbbox((0, 0), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.rectangle(
                [label_x, label_y, label_x + text_w + 8, label_y + text_h + 4],
                fill=color,
            )
            draw.text((label_x + 4, label_y), label, fill=(255, 255, 255), font=font)

    # 如果没有任何 OCR 位置信息，在图片底部添加提示
    if not ocr_words and paragraph_comments:
        try:
            font = _get_font(16)
        except Exception:
            font = ImageFont.load_default()
        msg = "提示：当前 OCR 引擎未返回文字位置，无法在原图上绘制批注框。"
        draw.text((10, img.height - 30), msg, fill=(255, 0, 0), font=font)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=95)
    return output.getvalue()
