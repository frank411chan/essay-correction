# -*- coding: utf-8 -*-
import asyncio
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models import Essay, Student
from app.schemas import BatchTaskResponse
from app.services.file_service import save_upload_file as save_file_to_uploads
from app.services.llm_service import correct_text
from app.services.ocr import get_ocr_provider
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/batch", tags=["batch"])

settings = get_settings()


def _parse_filename(filename: str) -> tuple:
    """解析文件名：人名_作文题目.jpg"""
    stem = Path(filename).stem
    # 支持 人名_题目 或 人名-题目
    match = re.match(r"^([^_-]+)[_-](.+)$", stem)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return stem.strip(), "未命名作文"


def _get_or_create_student(db: Session, name: str) -> Student:
    student = db.query(Student).filter(Student.name == name).first()
    if not student:
        student = Student(name=name)
        db.add(student)
        db.commit()
        db.refresh(student)
    return student


def _copy_image_to_uploads(source_path: Path) -> str:
    """将批量目录中的图片复制到 uploads 目录。"""
    from app.config import PROJECT_ROOT
    from app.services.file_service import UPLOAD_DIR

    ext = source_path.suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError(f"不支持的文件类型: {ext}")

    from PIL import Image
    import io
    import uuid

    img = Image.open(source_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

    filename = f"{uuid.uuid4().hex}.jpg"
    target_path = UPLOAD_DIR / filename

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85, optimize=True)
    with open(target_path, "wb") as f:
        f.write(output.getvalue())

    return str(target_path.relative_to(PROJECT_ROOT))


async def _do_batch_correct(task_id: str, essay_ids: list, db: Session):
    """后台批量批改。"""
    task_manager._tasks[task_id]["total"] = len(essay_ids)
    task_manager._tasks[task_id]["completed"] = 0
    task_manager._tasks[task_id]["failed"] = 0

    for essay_id in essay_ids:
        essay = db.query(Essay).filter(Essay.id == essay_id).first()
        if not essay:
            continue

        try:
            essay.status = "processing"
            db.commit()

            ocr_provider = get_ocr_provider(essay.ocr_engine)
            recognized_text = await ocr_provider.recognize(essay.image_path)

            result = await correct_text(
                recognized_text,
                essay.title,
                essay.grade,
                essay.genre,
            )

            essay.status = "done"
            essay.recognized_text = result.get("recognized_text")
            essay.total_score = result.get("total_score")
            essay.dimension_scores = result.get("dimension_scores")
            essay.comments = result.get("comments")
            essay.paragraph_comments = result.get("paragraph_comments")
            essay.suggestions = result.get("suggestions")
            essay.corrected_sentences = result.get("corrected_sentences")
            essay.error_message = None
            db.commit()

            task_manager._tasks[task_id]["completed"] += 1

        except Exception as e:
            essay.status = "failed"
            essay.error_message = str(e)
            db.commit()
            task_manager._tasks[task_id]["failed"] += 1

    task_manager.update_task(
        task_id,
        "done",
        f"批量批改完成，成功 {task_manager._tasks[task_id]['completed']}，失败 {task_manager._tasks[task_id]['failed']}",
    )


@router.post("/scan", response_model=BatchTaskResponse)
async def scan_directory(
    date: str = Query(..., description="日期，格式 YYYYMMDD"),
    ocr_engine: str = Query("kimi"),
    genre: str = Query("narrative"),
    auto_correct: bool = Query(True, description="是否扫描后自动批改"),
    db: Session = Depends(get_db),
):
    """扫描指定日期目录中的作文图片。"""
    scan_dir = Path(settings.batch_scan_dir) / date
    if not scan_dir.exists():
        raise HTTPException(status_code=404, detail=f"目录不存在: {scan_dir}")

    image_files = [f for f in scan_dir.iterdir() if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]

    if not image_files:
        raise HTTPException(status_code=404, detail="该目录下没有图片文件")

    essay_ids = []
    for image_file in image_files:
        try:
            student_name, title = _parse_filename(image_file.name)
            student = _get_or_create_student(db, student_name)
            image_path = _copy_image_to_uploads(image_file)

            essay = Essay(
                title=title,
                grade=student.grade or "初中",
                image_path=image_path,
                student_id=student.id,
                student_name=student.name,
                ocr_engine=ocr_engine,
                genre=genre,
                submitted_date=date,
                status="pending" if auto_correct else "done",
            )
            db.add(essay)
            db.commit()
            db.refresh(essay)
            essay_ids.append(essay.id)
        except Exception as e:
            print(f"处理文件 {image_file.name} 失败: {e}")
            continue

    task_id = task_manager.create_task(0)
    task_manager._tasks[task_id]["total"] = len(essay_ids)
    task_manager._tasks[task_id]["completed"] = 0
    task_manager._tasks[task_id]["failed"] = 0
    task_manager._tasks[task_id]["essays"] = essay_ids
    task_manager._tasks[task_id]["message"] = f"扫描完成，共 {len(essay_ids)} 篇作文"

    if auto_correct and essay_ids:
        task_manager.update_task(task_id, "processing", "开始批量批改...")
        asyncio.create_task(_do_batch_correct(task_id, essay_ids, db))
    else:
        task_manager.update_task(task_id, "done", "扫描完成，未启动自动批改")

    return {
        "task_id": task_id,
        "status": task_manager.get_task(task_id)["status"],
        "total": len(essay_ids),
        "completed": 0,
        "failed": 0,
        "essays": essay_ids,
        "message": task_manager.get_task(task_id)["message"],
    }


@router.post("/today", response_model=BatchTaskResponse)
async def scan_today(
    ocr_engine: str = Query("kimi"),
    genre: str = Query("narrative"),
    auto_correct: bool = Query(True),
    db: Session = Depends(get_db),
):
    """扫描当天目录。"""
    today = datetime.now().strftime("%Y%m%d")
    return await scan_directory(today, ocr_engine, genre, auto_correct, db)


@router.get("/tasks/{task_id}", response_model=BatchTaskResponse)
async def get_batch_task(task_id: str):
    """查询批量任务进度。"""
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    return {
        "task_id": task_id,
        "status": task["status"],
        "total": task.get("total", 0),
        "completed": task.get("completed", 0),
        "failed": task.get("failed", 0),
        "essays": task.get("essays", []),
        "message": task.get("message", ""),
    }
