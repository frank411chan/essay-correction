# -*- coding: utf-8 -*-
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import BatchTaskResponse
from app.services.batch_service import scan_directory
from app.services.task_manager import task_manager

router = APIRouter(prefix="/api/batch", tags=["batch"])


@router.post("/scan", response_model=BatchTaskResponse)
async def scan_batch(
    date: str = Query(..., description="日期，格式 YYYYMMDD"),
    ocr_engine: str = Query("kimi"),
    genre: Optional[str] = Query(None, description="文体模板，不填则不使用文体规则"),
    auto_correct: bool = Query(True, description="是否扫描后自动批改"),
):
    """扫描指定日期目录中的作文图片。"""
    try:
        result = await scan_directory(date, ocr_engine, genre, auto_correct)
        return result
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描失败: {str(e)}")


@router.post("/today", response_model=BatchTaskResponse)
async def scan_today(
    ocr_engine: str = Query("kimi"),
    genre: Optional[str] = Query(None, description="文体模板，不填则不使用文体规则"),
    auto_correct: bool = Query(True),
):
    """扫描当天目录。"""
    from datetime import datetime
    today = datetime.now().strftime("%Y%m%d")
    return await scan_batch(today, ocr_engine, genre, auto_correct)


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
