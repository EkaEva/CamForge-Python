# -*- mode: python ; coding: utf-8 -*-
"""
CamForge PyInstaller 打包配置
生成单个 CamForge.exe（无需 Python 环境即可运行）
"""

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# --- matplotlib 数据文件（字体、样式表等，运行时必需） ---
mpl_datas = collect_data_files('matplotlib')

# --- 隐式导入（PyInstaller 静态分析无法检测到的模块） ---
hidden_imports = [
    # matplotlib TkAgg 后端（matplotlib.use('TkAgg') 动态调度，静态分析会遗漏）
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends._backend_tk',
    # 条件导入的包（try/except ImportError，静态分析会遗漏）
    'PIL',
    'PIL.Image',
    'openpyxl',
    'openpyxl.utils',
    # 显式包含 numpy（确保 C 扩展被打包）
    'numpy',
    'numpy._core',
    'numpy._core._methods',
    'numpy._core._dtype_ctypes',
]

# 收集所有 matplotlib 后端子模块（防止遗漏）
hidden_imports += collect_submodules('matplotlib.backends')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=mpl_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不需要的大型标准库模块，减小体积
        'tkinter.test',
        'test',
        'unittest',
        'email',
        'html',
        'http',
        'xmlrpc',
        'pydoc',
        'distutils',
        'setuptools',
        'pip',
        'wheel',
        'lib2to3',
        'multiprocessing',
        'concurrent',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CamForge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,               # GUI 应用，不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='camforge.ico',         # 应用图标
)
