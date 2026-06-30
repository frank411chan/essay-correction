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


class SuggestionItem(BaseModel):
    problem: str = Field(..., description="具体问题")
    advice: str = Field(..., description="具体修改建议")
    original: str = Field(..., description="文中原文片段")
    suggested: str = Field(..., description="建议修改后的片段")


class TypoItem(BaseModel):
    wrong: str
    correct: str


class SentenceCorrection(BaseModel):
    original: str
    corrected: str


class ParagraphReview(BaseModel):
    paragraph_index: str
    original: str
    comment: str
    typos: List[TypoItem] = Field(default_factory=list)
    sentence_corrections: List[SentenceCorrection] = Field(default_factory=list)


class TopicAnalysis(BaseModel):
    topic_keywords: List[str] = Field(default_factory=list)
    core_requirements: str
    writing_focus: str
    common_pitfalls: str
    grading_emphasis: str


class DeepDiagnosis(BaseModel):
    problem: str
    cause: str
    suggestion: str


class WritingImprovement(BaseModel):
    example_author: str = ""
    example_analysis: str = ""
    summary: str = ""


class EssayResult(BaseModel):
    recognized_text: str
    total_score: int = Field(..., ge=0, le=100)
    shenzhen_score: int = Field(0, ge=0, le=45, description="深圳中考作文得分 0-45")
    shenzhen_level: Optional[str] = None
    dimension_scores: DimensionScores
    comments: Comments
    paragraph_comments: List[ParagraphComment]
    suggestions: List[SuggestionItem]
    corrected_sentences: List[CorrectedSentence]
    topic_analysis: Optional[TopicAnalysis] = None
    general_requirements: Optional[str] = None
    paragraph_reviews: List[ParagraphReview] = Field(default_factory=list)
    highlights: List[str] = Field(default_factory=list)
    deep_diagnosis: Optional[DeepDiagnosis] = None
    writing_improvement: Optional[WritingImprovement] = None


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
    genre: Optional[str] = None
    submitted_date: Optional[str] = None


class EssayCreate(EssayBase):
    pass


class RecognizedTextUpdate(BaseModel):
    recognized_text: str


class EssayResponse(EssayBase):
    id: int
    image_path: str
    image_paths: Optional[List[str]] = None
    student_name: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    recognized_text: Optional[str] = None
    ocr_words: Optional[List[Dict[str, Any]]] = None
    total_score: Optional[int] = None
    shenzhen_score: Optional[int] = None
    shenzhen_level: Optional[str] = None
    shenzhen_score_first: Optional[int] = None
    shenzhen_score_second: Optional[int] = None
    shenzhen_score_third: Optional[int] = None
    dimension_scores: Optional[Dict[str, Any]] = None
    comments: Optional[Dict[str, Any]] = None
    paragraph_comments: Optional[List[Dict[str, Any]]] = None
    suggestions: Optional[List[Any]] = None
    corrected_sentences: Optional[List[Dict[str, Any]]] = None
    topic_analysis: Optional[Dict[str, Any]] = None
    general_requirements: Optional[str] = None
    paragraph_reviews: Optional[List[Dict[str, Any]]] = None
    highlights: Optional[List[str]] = None
    deep_diagnosis: Optional[Dict[str, Any]] = None
    writing_improvement: Optional[Dict[str, Any]] = None
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
