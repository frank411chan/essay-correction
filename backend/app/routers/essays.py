# -*- coding: utf-8 -*-
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from typing import List
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Essay, Student
from app.schemas import (
    CorrectionTaskResponse,
    EssayListResponse,
    EssayResponse,
    EssayStatusResponse,
    RecognizedTextUpdate,
)
from app.services.annotation_service import generate_annotated_image
from app.services.file_service import get_image_path, save_upload_file, save_upload_files
from app.services.llm_service import analyze_topic, correct_text
from app.services.ocr import get_ocr_provider
from app.services.pdf_service import generate_pdf
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/essays", tags=["essays"])


def _get_student_or_fail(db: Session, student_id: Optional[int]) -> Optional[Student]:
    if not student_id:
        return None
    student = db.query(Student).filter(Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    return student


@router.post("/upload", response_model=EssayResponse)
async def upload_essay(
    file: UploadFile = File(None),
    files: List[UploadFile] = File(None),
    title: Optional[str] = Form(None),
    grade: str = Form("初中"),
    student_id: Optional[int] = Form(None),
    ocr_engine: str = Form("kimi"),
    genre: Optional[str] = Form(None),
    submitted_date: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """上传作文图片，创建待批改记录。支持单张或多张图片（最多3张）。"""
    student = _get_student_or_fail(db, student_id)

    # 兼容旧版单文件参数，优先使用 files
    upload_files = files if files and len(files) > 0 else ([file] if file else [])
    if not upload_files:
        raise HTTPException(status_code=400, detail="请上传至少一张作文图片")

    try:
        image_paths = save_upload_files(upload_files)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存图片失败: {str(e)}")

    essay = Essay(
        title=title,
        grade=grade,
        image_path=image_paths[0],
        image_paths=image_paths,
        student_id=student_id,
        student_name=student.name if student else None,
        ocr_engine=ocr_engine,
        genre=genre,
        submitted_date=submitted_date,
        status="pending",
    )
    db.add(essay)
    db.commit()
    db.refresh(essay)

    return essay


async def _do_correct(essay_id: int, task_id: str, db: Session):
    """后台执行批改任务。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        task_manager.update_task(task_id, "failed", "作文记录不存在")
        return

    try:
        essay.status = "processing"
        db.commit()
        task_manager.update_task(task_id, "processing", "正在进行 OCR 识别...")

        # OCR 识别（支持多图）
        ocr_provider = get_ocr_provider(essay.ocr_engine)
        image_paths = essay.image_paths if essay.image_paths else [essay.image_path]
        if len(image_paths) > 1:
            ocr_result = await ocr_provider.recognize_multiple(image_paths)
        else:
            ocr_result = await ocr_provider.recognize(image_paths[0])
        recognized_text = ocr_result.text

        # 保存 OCR 位置信息
        if ocr_result.words:
            essay.ocr_words = [
                {"text": w.text, "location": w.location} for w in ocr_result.words
            ]
        else:
            essay.ocr_words = []

        task_manager.update_task(task_id, "processing", "正在进行审题分析...")

        # 1. 审题
        topic_analysis = await analyze_topic(essay.title, essay.grade, essay.genre)

        task_manager.update_task(task_id, "processing", "正在进行作文批改...")

        # 2. 结合审题结果进行批改
        result = await correct_text(
            recognized_text,
            essay.title,
            essay.grade,
            essay.genre,
            topic_analysis,
        )

        # 更新数据库
        essay.status = "done"
        essay.recognized_text = result.get("recognized_text")
        essay.total_score = result.get("total_score")
        essay.shenzhen_score = result.get("shenzhen_score")
        essay.shenzhen_level = result.get("shenzhen_level")
        essay.shenzhen_score_first = result.get("shenzhen_score_first")
        essay.shenzhen_score_second = result.get("shenzhen_score_second")
        essay.shenzhen_score_third = result.get("shenzhen_score_third")
        essay.dimension_scores = result.get("dimension_scores")
        essay.comments = result.get("comments")
        essay.paragraph_comments = result.get("paragraph_comments")
        essay.suggestions = result.get("suggestions")
        essay.corrected_sentences = result.get("corrected_sentences")
        essay.topic_analysis = result.get("topic_analysis")
        essay.general_requirements = result.get("general_requirements")
        essay.paragraph_reviews = result.get("paragraph_reviews")
        essay.highlights = result.get("highlights")
        essay.deep_diagnosis = result.get("deep_diagnosis")
        essay.writing_improvement = result.get("writing_improvement")
        essay.error_message = None

        db.commit()
        task_manager.update_task(task_id, "done", "批改完成")

    except Exception as e:
        essay.status = "failed"
        essay.error_message = str(e)
        db.commit()
        task_manager.update_task(task_id, "failed", str(e))


@router.post("/{essay_id}/correct", response_model=CorrectionTaskResponse)
async def correct_essay_endpoint(essay_id: int, db: Session = Depends(get_db)):
    """触发异步批改，返回任务 ID。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    if essay.status == "processing":
        raise HTTPException(status_code=400, detail="作文正在批改中，请勿重复提交")

    task_id = task_manager.create_task(essay_id)

    # 启动后台任务
    import asyncio
    asyncio.create_task(_do_correct(essay_id, task_id, db))

    return {"task_id": task_id, "essay_id": essay_id, "status": "processing"}


async def _do_re_correct(essay_id: int, task_id: str, db: Session):
    """后台执行重新批改任务（使用当前 recognized_text，不再 OCR）。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        task_manager.update_task(task_id, "failed", "作文记录不存在")
        return

    try:
        essay.status = "processing"
        db.commit()
        task_manager.update_task(task_id, "processing", "正在进行重新批改...")

        if not essay.recognized_text:
            raise ValueError("没有可批改的识别文本，请先上传或编辑识别内容")

        # 1. 审题
        task_manager.update_task(task_id, "processing", "正在进行审题分析...")
        topic_analysis = await analyze_topic(essay.title, essay.grade, essay.genre)

        # 2. 结合审题结果进行批改（双评）
        task_manager.update_task(task_id, "processing", "正在进行作文批改...")
        result = await correct_text(
            essay.recognized_text,
            essay.title,
            essay.grade,
            essay.genre,
            topic_analysis,
        )

        # 更新数据库
        essay.status = "done"
        essay.recognized_text = result.get("recognized_text")
        essay.total_score = result.get("total_score")
        essay.shenzhen_score = result.get("shenzhen_score")
        essay.shenzhen_level = result.get("shenzhen_level")
        essay.shenzhen_score_first = result.get("shenzhen_score_first")
        essay.shenzhen_score_second = result.get("shenzhen_score_second")
        essay.shenzhen_score_third = result.get("shenzhen_score_third")
        essay.dimension_scores = result.get("dimension_scores")
        essay.comments = result.get("comments")
        essay.paragraph_comments = result.get("paragraph_comments")
        essay.suggestions = result.get("suggestions")
        essay.corrected_sentences = result.get("corrected_sentences")
        essay.topic_analysis = result.get("topic_analysis")
        essay.general_requirements = result.get("general_requirements")
        essay.paragraph_reviews = result.get("paragraph_reviews")
        essay.highlights = result.get("highlights")
        essay.deep_diagnosis = result.get("deep_diagnosis")
        essay.writing_improvement = result.get("writing_improvement")
        essay.error_message = None

        db.commit()
        task_manager.update_task(task_id, "done", "重新批改完成")

    except Exception as e:
        essay.status = "failed"
        essay.error_message = str(e)
        db.commit()
        task_manager.update_task(task_id, "failed", str(e))


@router.put("/{essay_id}/recognized-text", response_model=EssayResponse)
async def update_recognized_text(
    essay_id: int,
    data: RecognizedTextUpdate,
    db: Session = Depends(get_db),
):
    """更新识别文本（用于人工校对 OCR 结果）。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    essay.recognized_text = data.recognized_text
    db.commit()
    db.refresh(essay)
    return essay


@router.post("/{essay_id}/re-correct", response_model=CorrectionTaskResponse)
async def re_correct_essay_endpoint(essay_id: int, db: Session = Depends(get_db)):
    """使用当前识别文本触发重新批改（不重新 OCR），返回任务 ID。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    if essay.status == "processing":
        raise HTTPException(status_code=400, detail="作文正在批改中，请勿重复提交")

    if not essay.recognized_text:
        raise HTTPException(status_code=400, detail="没有可批改的识别文本")

    task_id = task_manager.create_task(essay_id)

    # 启动后台任务
    import asyncio
    asyncio.create_task(_do_re_correct(essay_id, task_id, db))

    return {"task_id": task_id, "essay_id": essay_id, "status": "processing"}


@router.get("/{essay_id}/status", response_model=EssayStatusResponse)
async def get_essay_status(essay_id: int, db: Session = Depends(get_db)):
    """获取作文批改状态。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    return {
        "id": essay.id,
        "status": essay.status,
        "error_message": essay.error_message,
        "result": essay if essay.status == "done" else None,
    }


@router.get("/{essay_id}", response_model=EssayResponse)
async def get_essay(essay_id: int, db: Session = Depends(get_db)):
    """获取作文详情及批改结果。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")
    return essay


@router.get("/{essay_id}/image")
async def get_essay_image(
    essay_id: int,
    index: int = Query(0, ge=0, description="图片索引，从0开始"),
    db: Session = Depends(get_db),
):
    """获取作文原始图片。支持多图时通过 index 指定第几张。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    image_paths = essay.image_paths if essay.image_paths else [essay.image_path]
    if index >= len(image_paths):
        raise HTTPException(status_code=404, detail="图片索引超出范围")

    path = get_image_path(image_paths[index])
    if not path.exists():
        raise HTTPException(status_code=404, detail="图片文件不存在")

    return FileResponse(path)


@router.get("/{essay_id}/annotated-image")
async def get_essay_annotated_image(essay_id: int, db: Session = Depends(get_db)):
    """获取带批注高亮的作文图片。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    if essay.status != "done":
        raise HTTPException(status_code=400, detail="作文尚未批改完成，无法生成批注图")

    try:
        image_bytes = generate_annotated_image(essay)
        return StreamingResponse(
            iter([image_bytes]),
            media_type="image/jpeg",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批注图生成失败: {str(e)}")


@router.get("/{essay_id}/pdf")
async def get_essay_pdf(essay_id: int, db: Session = Depends(get_db)):
    """导出 PDF 批改报告。"""
    essay = db.query(Essay).filter(Essay.id == essay_id).first()
    if not essay:
        raise HTTPException(status_code=404, detail="作文记录不存在")

    if essay.status != "done":
        raise HTTPException(status_code=400, detail="作文尚未批改完成，无法导出 PDF")

    try:
        pdf_bytes = generate_pdf(essay)
        filename = f"{essay.student_name or '未知'}_{essay.title or '作文'}_批改报告.pdf"
        # RFC 5987 编码中文文件名
        from urllib.parse import quote
        encoded_filename = quote(filename)
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF 生成失败: {str(e)}")


@router.get("", response_model=EssayListResponse)
async def list_essays(
    skip: int = 0,
    limit: int = 20,
    student_name: Optional[str] = Query(None),
    title: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """获取作文历史列表，支持多条件查询。"""
    query = db.query(Essay)

    if student_name:
        query = query.filter(Essay.student_name.ilike(f"%{student_name}%"))
    if title:
        query = query.filter(or_(Essay.title.ilike(f"%{title}%"), Essay.title.is_(None)))
    if date:
        query = query.filter(Essay.submitted_date == date)
    if status:
        query = query.filter(Essay.status == status)

    total = query.count()
    items = query.order_by(Essay.created_at.desc()).offset(skip).limit(limit).all()
    return {"total": total, "items": items}
