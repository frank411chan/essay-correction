# -*- coding: utf-8 -*-
"""启动后端服务，脱离当前会话。"""
import os
import subprocess
import sys


def main():
    backend_dir = os.path.join(os.path.dirname(__file__), "backend")
    log_path = os.path.join(os.path.dirname(__file__), "backend.log")

    # 使用 venv 中的 Python
    python_path = os.path.join(backend_dir, "venv", "bin", "python")
    if not os.path.exists(python_path):
        python_path = sys.executable

    # 使用 start_new_session 脱离父进程
    with open(log_path, "a") as log_file:
        process = subprocess.Popen(
            [python_path, "run.py"],
            cwd=backend_dir,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    print(f"后端服务已启动，PID: {process.pid}")
    print(f"日志: {log_path}")


if __name__ == "__main__":
    main()
