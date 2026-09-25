#!/usr/bin/env python3
"""Prompt without echo; passwords exist only in process memory."""
import getpass
import os
from education import MODULES
from build_static_site import build

if __name__ == "__main__":
    for module in MODULES.values():
        password = getpass.getpass(f"{module['title']}密码：")
        if not password:
            raise SystemExit("密码不能为空。")
        if password != getpass.getpass("再次输入："):
            raise SystemExit("两次密码不一致。")
        os.environ[module["password_env"]] = password
    try:
        build()
        print("两个模块已加密，网站已构建。")
    finally:
        for module in MODULES.values():
            os.environ.pop(module["password_env"], None)
