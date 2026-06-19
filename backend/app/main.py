# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import essays, students, batch

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="作文批改系统",
    description="基于 Kimi 多模态大模型的作文图片识别与批改系统",
    version="0.1.0",
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
    return {"status": "ok"}
