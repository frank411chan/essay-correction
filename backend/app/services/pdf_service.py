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
    KeepTogether,
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


def _create_style(name, font_size=10, alignment=0, space_after=6, bold=False, text_color="#303133"):
    return ParagraphStyle(
        name,
        fontName=CHINESE_FONT,
        fontSize=font_size,
        alignment=alignment,
        spaceAfter=space_after,
        leading=font_size + 4,
        textColor=colors.HexColor(text_color),
        wordWrap="CJK",
    )


def _safe_paragraph(text, style):
    """安全生成 Paragraph，处理 None 值。"""
    return Paragraph(str(text or "").replace("\n", "<br/>"), style)


def _build_section_title(title, style_name="Heading"):
    style = _create_style(style_name, font_size=14, space_after=8, bold=True, text_color="#000000")
    return Paragraph(f"<b>| {title}</b>", style)


def _build_bordered_card(content_list, bg_color="#ffffff"):
    """用表格模拟带边框卡片。"""
    data = [[content] for content in content_list]
    table = Table(data, colWidths=[16 * cm])
    table.setStyle(
        TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), CHINESE_FONT),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg_color)),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcdfe6")),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    return table


def generate_pdf(essay) -> bytes:
    """生成 PDF 批改报告，返回二进制内容。参照范文结构：亮点、诊断、精批细改、分数、写作提升。"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    title_style = _create_style("Title", font_size=22, alignment=1, space_after=8, bold=True)
    subtitle_style = _create_style("Subtitle", font_size=11, alignment=1, space_after=20, text_color="#606266")
    normal_style = _create_style("Normal", font_size=10, space_after=6)
    quote_style = _create_style("Quote", font_size=11, alignment=1, space_after=20, text_color="#303133")
    small_style = _create_style("Small", font_size=9, space_after=4, text_color="#606266")
    score_style = _create_style("Score", font_size=36, alignment=1, space_after=6, bold=True, text_color="#000000")

    story = []

    # 顶部信息
    story.append(Paragraph(f"{essay.student_name or '未知'}  作文辅导报告", title_style))
    info_text = f"年级：{essay.grade or '未设置'}　　标题：{essay.title or '未命名'}　　日期：{essay.submitted_date or '未设置'}"
    story.append(Paragraph(info_text, subtitle_style))

    # 题目引导语（如有识别文本且作文标题存在，取原文开头作为引导语）
    recognized = essay.recognized_text or ""
    if recognized:
        first_line = recognized.split("\n")[0].strip()[:80]
        if first_line:
            story.append(Paragraph(f"“{first_line}”", quote_style))

    story.append(Spacer(1, 0.3 * cm))

    # 本次亮点
    story.append(_build_section_title("本次亮点"))
    highlights = essay.highlights or []
    if not highlights and essay.comments:
        highlights = (essay.comments or {}).get("strengths", [])
    highlight_items = [Paragraph(f"• {h}", normal_style) for h in highlights]
    if not highlight_items:
        highlight_items = [Paragraph("暂无", small_style)]
    story.append(_build_bordered_card(highlight_items, bg_color="#f0f9ff"))
    story.append(Spacer(1, 0.6 * cm))

    # 深度诊断
    story.append(_build_section_title("深度诊断"))
    diagnosis = essay.deep_diagnosis or {}
    diagnosis_content = []
    if diagnosis.get("problem"):
        diagnosis_content.append(Paragraph(f"<b>问题表现：</b>{diagnosis['problem']}", normal_style))
    if diagnosis.get("cause"):
        diagnosis_content.append(Paragraph(f"<b>原因分析：</b>{diagnosis['cause']}", normal_style))
    if diagnosis.get("suggestion"):
        diagnosis_content.append(Paragraph(f"<b>改进方向：</b>{diagnosis['suggestion']}", normal_style))
    if not diagnosis_content:
        overall = (essay.comments or {}).get("overall", "")
        diagnosis_content.append(Paragraph(overall or "暂无", normal_style))
    story.append(_build_bordered_card(diagnosis_content, bg_color="#fff8f0"))
    story.append(Spacer(1, 0.6 * cm))

    # 参考分数
    story.append(_build_section_title("参考分数"))
    story.append(Paragraph("分数是一个记号，但学到的知识和经验将伴随你一生", small_style))
    story.append(Paragraph(f"{essay.total_score or 0} 分", score_style))

    # 分项得分
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
    story.append(PageBreak())

    # 精批细改（左右对照）
    story.append(_build_section_title("精批细改"))
    story.append(Spacer(1, 0.3 * cm))

    paragraph_reviews = essay.paragraph_reviews or []
    if not paragraph_reviews and essay.paragraph_comments:
        # 兼容旧数据：把 paragraph_comments 转成 paragraph_reviews
        for item in essay.paragraph_comments:
            paragraph_reviews.append({
                "paragraph_index": item.get("paragraph_index", 0),
                "original": "",
                "comment": item.get("comment", ""),
                "typos": [],
                "sentence_corrections": [],
            })

    for review in paragraph_reviews:
        original = review.get("original", "")
        comment = review.get("comment", "")
        typos = review.get("typos", [])
        sentence_corrections = review.get("sentence_corrections", [])

        # 左侧：段落原文
        left_elements = []
        left_elements.append(Paragraph(f"<b>第 {review.get('paragraph_index', 0)} 段原文</b>", normal_style))
        left_elements.append(_safe_paragraph(original, normal_style))
        left_table = Table([[c] for c in left_elements], colWidths=[8 * cm])
        left_table.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), CHINESE_FONT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#ebeef5")),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fafafa")),
            ])
        )

        # 右侧：段落批改
        right_content = []
        right_content.append(Paragraph(f"<b>第 {review.get('paragraph_index', 0)} 段批改</b>", normal_style))
        right_content.append(_safe_paragraph(comment, normal_style))

        if typos:
            right_content.append(Paragraph("<b>错别字：</b>", normal_style))
            for typo in typos:
                right_content.append(
                    Paragraph(
                        f"• “{typo.get('wrong', '')}” → “{typo.get('correct', '')}”",
                        small_style,
                    )
                )

        if sentence_corrections:
            right_content.append(Paragraph("<b>病句修改：</b>", normal_style))
            for sc in sentence_corrections:
                right_content.append(
                    Paragraph(
                        f"原：{sc.get('original', '')}<br/>改：{sc.get('corrected', '')}",
                        small_style,
                    )
                )

        right_table = Table([[c] for c in right_content], colWidths=[8 * cm])
        right_table.setStyle(
            TableStyle([
                ("FONTNAME", (0, 0), (-1, -1), CHINESE_FONT),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ])
        )

        row = [[left_table, right_table]]
        review_table = Table(row, colWidths=[8.5 * cm, 8.5 * cm])
        review_table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dcdfe6")),
            ])
        )

        # 每段尽量保持在一起，避免跨页断裂
        story.append(KeepTogether([review_table, Spacer(1, 0.4 * cm)]))

    # 写作提升
    writing = essay.writing_improvement or {}
    if writing.get("example_author") or writing.get("example_analysis") or writing.get("summary"):
        story.append(PageBreak())
        story.append(_build_section_title("写作提升"))
        story.append(Paragraph("学习名家写法，明确提升方向", small_style))
        if writing.get("example_author"):
            story.append(Paragraph(f"<b>{writing['example_author']}</b>", normal_style))
        if writing.get("example_analysis"):
            story.append(_safe_paragraph(writing["example_analysis"], normal_style))
        if writing.get("summary"):
            story.append(_safe_paragraph(writing["summary"], normal_style))

    # 兜底：旧版建议
    suggestions = essay.suggestions or []
    if suggestions and not writing.get("summary"):
        story.append(_build_section_title("改进建议"))
        for idx, item in enumerate(suggestions, 1):
            story.append(Paragraph(f"{idx}. {item}", normal_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
