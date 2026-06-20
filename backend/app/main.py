# -*- coding: utf-8 -*-
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import engine, Base
from app.routers import essays, students, batch
from app.services.batch_service import scan_today_directory

settings = get_settings()

# 创建数据库表
Base.metadata.create_all(bind=engine)


async def scheduled_scan():
    """定时扫描当天目录。"""
    try:
        print(f"[定时任务] 开始扫描当天目录: {settings.batch_scan_dir}")
        await scan_today_directory()
        print("[定时任务] 扫描完成")
    except Exception as e:
        print(f"[定时任务] 扫描失败: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。"""
    scheduler = None
    if settings.auto_scan_enabled:
        scheduler = AsyncIOScheduler()
        hour, minute = map(int, settings.auto_scan_time.split(":"))
        scheduler.add_job(
            scheduled_scan,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_scan",
            replace_existing=True,
        )
        scheduler.start()
        print(f"[定时任务] 已启用，每天 {settings.auto_scan_time} 扫描当天目录")
    else:
        print("[定时任务] 未启用")

    yield

    if scheduler:
        scheduler.shutdown()


app = FastAPI(
    title="作文批改系统",
    description="基于 Kimi 多模态大模型的作文图片识别与批改系统",
    version="0.2.0",
    lifespan=lifespan,
)

# 配置 CORS，允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(essays.router)
app.include_router(students.router)
app.include_router(batch.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}
