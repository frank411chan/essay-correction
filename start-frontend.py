# -*- coding: utf-8 -*-
"""启动前端服务，脱离当前会话。"""
import os
import subprocess
import sys


def main():
    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
    log_path = os.path.join(os.path.dirname(__file__), "frontend.log")

    with open(log_path, "a") as log_file:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )

    print(f"前端服务已启动，PID: {process.pid}")
    print(f"日志: {log_path}")


if __name__ == "__main__":
    main()
