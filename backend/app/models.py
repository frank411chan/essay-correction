# -*- coding: utf-8 -*-
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base


CHINA_TZ = ZoneInfo("Asia/Shanghai")


def now_china() -> datetime:
    """返回东八区（中国标准时间）当前时间。"""
    return datetime.now(CHINA_TZ)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    grade = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    student_no = Column(String, nullable=True)
    created_at = Column(DateTime, default=now_china)
    updated_at = Column(DateTime, default=now_china, onupdate=now_china)

    essays = relationship("Essay", back_populates="student", cascade="all, delete-orphan")


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True, index=True)
    grade = Column(String, default="初中")
    image_path = Column(String, nullable=False)
    image_paths = Column(JSON, nullable=True)  # 多图路径列表，按顺序组成一篇文章

    # 关联学生
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    student_name = Column(String, nullable=True, index=True)
    student = relationship("Student", back_populates="essays")

    # 批改配置
    ocr_engine = Column(String, default="kimi")  # kimi / baidu / tencent
    genre = Column(String, nullable=True, default=None)  # narrative / argumentation / description / prose，允许为空
    submitted_date = Column(String, nullable=True, index=True)  # 日期格式 YYYYMMDD

    # 状态
    status = Column(String, default="pending")  # pending / processing / done / failed
    error_message = Column(Text, nullable=True)

    # 结果
    recognized_text = Column(Text, nullable=True)
    ocr_words = Column(JSON, nullable=True)  # OCR 识别的文字位置信息
    total_score = Column(Integer, nullable=True)
    shenzhen_score = Column(Integer, nullable=True)  # 深圳中考作文得分 0-45
    shenzhen_level = Column(String, nullable=True)  # 档位
    shenzhen_score_first = Column(Integer, nullable=True)  # 双评第一评
    shenzhen_score_second = Column(Integer, nullable=True)  # 双评第二评
    shenzhen_score_third = Column(Integer, nullable=True)  # 三评（分差>3时）
    dimension_scores = Column(JSON, nullable=True)
    comments = Column(JSON, nullable=True)
    paragraph_comments = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    corrected_sentences = Column(JSON, nullable=True)

    # 新增：审题 + 段落精批 + 范文式结构
    topic_analysis = Column(JSON, nullable=True)  # 审题结果
    general_requirements = Column(Text, nullable=True)  # 本次使用的通用批改要求
    paragraph_reviews = Column(JSON, nullable=True)  # 段落级精批（含原文、错别字、病句）
    highlights = Column(JSON, nullable=True)  # 本次亮点
    deep_diagnosis = Column(JSON, nullable=True)  # 深度诊断
    writing_improvement = Column(JSON, nullable=True)  # 写作提升 / 名家范文

    created_at = Column(DateTime, default=now_china)
    updated_at = Column(DateTime, default=now_china, onupdate=now_china)
