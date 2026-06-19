# -*- coding: utf-8 -*-
import io
import os
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)

# 注册中文字体
FONT_PATHS = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/truetype/arphic/uming.ttc",
]

CHINESE_FONT = "Helvetica"
for font_path in FONT_PATHS:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont("ChineseFont", font_path))
            CHINESE_FONT = "ChineseFont"
            break
        except Exception:
            continue


def _create_style(name, font_size=10, alignment=0, space_after=6, bold=False):
    return ParagraphStyle(
        name,
        fontName=CHINESE_FONT,
        fontSize=font_size,
        alignment=alignment,
        spaceAfter=space_after,
        leading=font_size + 4,
        textColor=colors.HexColor("#303133"),
        wordWrap="CJK",
    )


def generate_pdf(essay) -> bytes:
    """生成 PDF 批改报告，返回二进制内容。"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = _create_style("Title", font_size=20, alignment=1, space_after=20, bold=True)
    heading_style = _create_style("Heading", font_size=14, space_after=10, bold=True)
    normal_style = _create_style("Normal", font_size=10, space_after=6)
    score_style = _create_style("Score", font_size=36, alignment=1, space_after=6, bold=True)
    small_style = _create_style("Small", font_size=9, space_after=4)

    story = []

    # 标题
    story.append(Paragraph("作文批改报告", title_style))
    story.append(Spacer(1, 0.5 * cm))

    # 基本信息
    info_data = [
        ["学生", essay.student_name or "未知", "年级", essay.grade or "未设置"],
        ["标题", essay.title or "未命名", "日期", essay.submitted_date or "未设置"],
        ["OCR 引擎", essay.ocr_engine or "kimi", "文体", essay.genre or "narrative"],
    ]
    info_table = Table(info_data, colWidths=[3 * cm, 5 * cm, 3 * cm, 5 * cm])
    info_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), CHINESE_FONT),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f7fa")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#606266")),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcdfe6")),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    story.append(info_table)
    story.append(Spacer(1, 0.8 * cm))

    # 总分
    story.append(Paragraph("总分", heading_style))
    story.append(Paragraph(str(essay.total_score or 0), score_style))
    story.append(Spacer(1, 0.5 * cm))

    # 分项得分
    story.append(Paragraph("分项得分", heading_style))
    dim = essay.dimension_scores or {}
    score_data = [
        ["内容", "结构", "语言", "书写"],
        [
            str(dim.get("content", 0)),
            str(dim.get("structure", 0)),
            str(dim.get("language", 0)),
            str(dim.get("writing", 0)),
        ],
    ]
    score_table = Table(score_data, colWidths=[4 * cm] * 4)
    score_table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), CHINESE_FONT),
            ("FONTSIZE", (0, 0), (0, 0), 10),
            ("FONTSIZE", (0, 1), (-1, 1), 14),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#409eff")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#ecf5ff")),
            ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#409eff")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcdfe6")),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    story.append(score_table)
    story.append(Spacer(1, 0.8 * cm))

    # 总体评语
    story.append(Paragraph("总体评语", heading_style))
    comments = essay.comments or {}
    story.append(Paragraph(comments.get("overall", ""), normal_style))
    story.append(Spacer(1, 0.3 * cm))

    # 优点
    story.append(Paragraph("优点", heading_style))
    for item in comments.get("strengths", []):
        story.append(Paragraph(f"• {item}", normal_style))
    story.append(Spacer(1, 0.3 * cm))

    # 不足
    story.append(Paragraph("不足", heading_style))
    for item in comments.get("weaknesses", []):
        story.append(Paragraph(f"• {item}", normal_style))
    story.append(PageBreak())

    # 识别文本
    story.append(Paragraph("识别文本", heading_style))
    story.append(Paragraph(essay.recognized_text or "", small_style))
    story.append(Spacer(1, 0.5 * cm))

    # 段落批注
    story.append(Paragraph("段落批注", heading_style))
    for item in essay.paragraph_comments or []:
        story.append(
            Paragraph(
                f"<b>第 {item.get('paragraph_index', 0)} 段：</b>{item.get('comment', '')}",
                normal_style,
            )
        )
    story.append(Spacer(1, 0.5 * cm))

    # 改进建议
    story.append(Paragraph("改进建议", heading_style))
    for idx, item in enumerate(essay.suggestions or [], 1):
        story.append(Paragraph(f"{idx}. {item}", normal_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
