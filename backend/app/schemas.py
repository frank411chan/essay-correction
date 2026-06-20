# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DimensionScores(BaseModel):
    content: int = Field(..., ge=0, le=30, description="内容得分")
    structure: int = Field(..., ge=0, le=20, description="结构得分")
    language: int = Field(..., ge=0, le=25, description="语言得分")
    writing: int = Field(..., ge=0, le=25, description="书写得分")


class Comments(BaseModel):
    overall: str
    strengths: List[str]
    weaknesses: List[str]


class ParagraphComment(BaseModel):
    paragraph_index: int
    comment: str


class CorrectedSentence(BaseModel):
    original: str
    corrected: str


class EssayResult(BaseModel):
    recognized_text: str
    total_score: int = Field(..., ge=0, le=100)
    dimension_scores: DimensionScores
    comments: Comments
    paragraph_comments: List[ParagraphComment]
    suggestions: List[str]
    corrected_sentences: List[CorrectedSentence]


# ============= Student Schemas =============

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    grade: Optional[str] = None
    class_name: Optional[str] = None
    student_no: Optional[str] = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(StudentBase):
    pass


class StudentResponse(StudentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudentListResponse(BaseModel):
    total: int
    items: List[StudentResponse]


# ============= Essay Schemas =============

class EssayBase(BaseModel):
    title: Optional[str] = None
    grade: str = "初中"
    student_id: Optional[int] = None
    ocr_engine: str = "kimi"
    genre: str = "narrative"
    submitted_date: Optional[str] = None


class EssayCreate(EssayBase):
    pass


class EssayResponse(EssayBase):
    id: int
    image_path: str
    student_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    recognized_text: Optional[str] = None
    ocr_words: Optional[List[Dict[str, Any]]] = None
    total_score: Optional[int] = None
    dimension_scores: Optional[Dict[str, Any]] = None
    comments: Optional[Dict[str, Any]] = None
    paragraph_comments: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[str]] = None
    corrected_sentences: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EssayListResponse(BaseModel):
    total: int
    items: List[EssayResponse]


class EssayStatusResponse(BaseModel):
    id: int
    status: str
    error_message: Optional[str] = None
    result: Optional[EssayResponse] = None


# ============= Task Schemas =============

class CorrectionTaskResponse(BaseModel):
    task_id: str
    essay_id: int
    status: str


class BatchTaskResponse(BaseModel):
    task_id: str
    status: str
    total: int = 0
    completed: int = 0
    failed: int = 0
    essays: List[int] = []
    message: Optional[str] = None
