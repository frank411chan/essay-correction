# -*- coding: utf-8 -*-
import uuid
import asyncio
from typing import Dict, Optional
from datetime import datetime


class TaskManager:
    """内存中的异步任务状态管理器。"""

    def __init__(self):
        self._tasks: Dict[str, dict] = {}

    def create_task(self, essay_id: int) -> str:
        task_id = str(uuid.uuid4())
        self._tasks[task_id] = {
            "task_id": task_id,
            "essay_id": essay_id,
            "status": "processing",
            "message": "",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        return task_id

    def get_task(self, task_id: str) -> Optional[dict]:
        return self._tasks.get(task_id)

    def update_task(self, task_id: str, status: str, message: str = ""):
        if task_id in self._tasks:
            self._tasks[task_id]["status"] = status
            self._tasks[task_id]["message"] = message
            self._tasks[task_id]["updated_at"] = datetime.utcnow().isoformat()

    def delete_task(self, task_id: str):
        self._tasks.pop(task_id, None)


task_manager = TaskManager()
