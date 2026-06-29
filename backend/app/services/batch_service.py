# -*- coding: utf-8 -*-
"""批量扫描服务，供路由和定时任务共用。"""
import asyncio
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy.orm import Session

from app.config import get_settings, PROJECT_ROOT
from app.database import SessionLocal
from app.models import Essay, Student
from app.services.file_service import UPLOAD_DIR
from app.services.llm_service import correct_text
from app.services.ocr import get_ocr_provider
from app.services.task_manager import task_manager

settings = get_settings()


def _parse_filename(filename: str) -> tuple:
    """解析文件名：人名_作文题目_序号.jpg 或 人名_作文题目.jpg

    返回：(姓名, 作文题目, 序号)
    """
    stem = Path(filename).stem
    # 先尝试匹配 姓名_题目_序号
    match = re.match(r"^([^_]+)_(.+?)_(\d+)$", stem)
    if match:
        return match.group(1).strip(), match.group(2).strip(), int(match.group(3))

    # 再尝试匹配 姓名_题目
    match = re.match(r"^([^_]+)_(.+)$", stem)
    if match:
        return match.group(1).strip(), match.group(2).strip(), 1

    return stem.strip(), "未命名作文", 1


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
    from PIL import Image
    import io

    ext = source_path.suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise ValueError(f"不支持的文件类型: {ext}")

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


async def _do_batch_correct(task_id: str, essay_ids: List[int]):
    """后台批量批改。"""
    db = SessionLocal()
    try:
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
                image_paths = essay.image_paths if essay.image_paths else [essay.image_path]
                if len(image_paths) > 1:
                    ocr_result = await ocr_provider.recognize_multiple(image_paths)
                else:
                    ocr_result = await ocr_provider.recognize(image_paths[0])
                recognized_text = ocr_result.text

                if ocr_result.words:
                    essay.ocr_words = [
                        {"text": w.text, "location": w.location} for w in ocr_result.words
                    ]
                else:
                    essay.ocr_words = []

                result = await correct_text(
                    recognized_text,
                    essay.title,
                    essay.grade,
                    essay.genre,
                )

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
    finally:
        db.close()


async def scan_directory(
    date: str,
    ocr_engine: str = "kimi",
    genre: Optional[str] = None,
    auto_correct: bool = True,
) -> dict:
    """扫描指定日期目录中的作文图片。"""
    scan_dir = Path(settings.batch_scan_dir) / date
    if not scan_dir.exists():
        raise FileNotFoundError(f"目录不存在: {scan_dir}")

    image_files = [f for f in scan_dir.iterdir() if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]

    if not image_files:
        raise FileNotFoundError("该目录下没有图片文件")

    # 按姓名_题目分组，组内按序号排序
    groups: dict[tuple[str, str], list[tuple[int, Path]]] = {}
    for image_file in image_files:
        try:
            student_name, title, seq = _parse_filename(image_file.name)
            groups.setdefault((student_name, title), []).append((seq, image_file))
        except Exception as e:
            print(f"解析文件名 {image_file.name} 失败: {e}")
            continue

    # 每组按序号排序，最多取3张
    for key in groups:
        groups[key].sort(key=lambda x: x[0])
        groups[key] = groups[key][:3]

    db = SessionLocal()
    try:
        essay_ids = []
        for (student_name, title), items in groups.items():
            try:
                student = _get_or_create_student(db, student_name)
                image_paths = [_copy_image_to_uploads(item[1]) for item in items]

                essay = Essay(
                    title=title,
                    grade=student.grade or "初中",
                    image_path=image_paths[0],
                    image_paths=image_paths,
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
                print(f"处理文件组 {student_name}_{title} 失败: {e}")
                continue

        task_id = task_manager.create_task(0)
        task_manager._tasks[task_id]["total"] = len(essay_ids)
        task_manager._tasks[task_id]["completed"] = 0
        task_manager._tasks[task_id]["failed"] = 0
        task_manager._tasks[task_id]["essays"] = essay_ids
        task_manager._tasks[task_id]["message"] = f"扫描完成，共 {len(essay_ids)} 篇作文"

        if auto_correct and essay_ids:
            task_manager.update_task(task_id, "processing", "开始批量批改...")
            asyncio.create_task(_do_batch_correct(task_id, essay_ids))
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
    finally:
        db.close()


async def scan_today_directory() -> dict:
    """扫描当天目录。"""
    today = datetime.now().strftime("%Y%m%d")
    return await scan_directory(today, "kimi", None, True)
