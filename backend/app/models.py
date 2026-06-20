# -*- coding: utf-8 -*-
from datetime import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import relationship
from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    grade = Column(String, nullable=True)
    class_name = Column(String, nullable=True)
    student_no = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    essays = relationship("Essay", back_populates="student", cascade="all, delete-orphan")


class Essay(Base):
    __tablename__ = "essays"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=True, index=True)
    grade = Column(String, default="初中")
    image_path = Column(String, nullable=False)

    # 关联学生
    student_id = Column(Integer, ForeignKey("students.id"), nullable=True, index=True)
    student_name = Column(String, nullable=True, index=True)
    student = relationship("Student", back_populates="essays")

    # 批改配置
    ocr_engine = Column(String, default="kimi")  # kimi / baidu / tencent
    genre = Column(String, default="narrative")  # narrative / argumentation / description / prose
    submitted_date = Column(String, nullable=True, index=True)  # 日期格式 YYYYMMDD

    # 状态
    status = Column(String, default="pending")  # pending / processing / done / failed
    error_message = Column(Text, nullable=True)

    # 结果
    recognized_text = Column(Text, nullable=True)
    ocr_words = Column(JSON, nullable=True)  # OCR 识别的文字位置信息
    total_score = Column(Integer, nullable=True)
    dimension_scores = Column(JSON, nullable=True)
    comments = Column(JSON, nullable=True)
    paragraph_comments = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    corrected_sentences = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
