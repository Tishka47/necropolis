# -*- mode: python ; coding: utf-8 -*-
# Сборка Necropolis.exe: клиент Kivy + встроенный сервер FastAPI в одном файле.
# Запуск: packaging\build_exe.bat (или: pyinstaller packaging\necropolis.spec)
import os
import sys

from kivy_deps import angle, glew, sdl2
from kivy.tools.packaging.pyinstaller_hooks import get_deps_minimal, hookspath, runtime_hooks
from PyInstaller.utils.hooks import collect_submodules

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
CLIENT = os.path.join(ROOT, "client")
BACKEND = os.path.join(ROOT, "backend")
sys.path.insert(0, BACKEND)  # чтобы collect_submodules нашёл пакет app

deps = get_deps_minimal(video=None, audio=None, camera=None, spelling=None)
deps["hiddenimports"] = (
    deps.get("hiddenimports", [])
    + collect_submodules("app")          # серверная часть (FastAPI) из папки backend
    + collect_submodules("uvicorn")      # uvicorn подключает протоколы и циклы по имени
    + collect_submodules("sqlalchemy.dialects.sqlite")
)

a = Analysis(
    [os.path.join(CLIENT, "main.py")],
    pathex=[CLIENT, BACKEND],
    datas=[
        (os.path.join(CLIENT, "kv"), "kv"),
        (os.path.join(CLIENT, "fonts"), "fonts"),
    ],
    hookspath=hookspath(),
    runtime_hooks=runtime_hooks(),
    noarchive=False,
    **deps,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins + angle.dep_bins)],
    name="Necropolis",
    console=False,
    upx=False,
)
