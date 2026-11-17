# -*- mode: python ; coding: utf-8 -*-
import importlib.metadata
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, copy_metadata

block_cipher = None

try:
    app_version = os.environ.get("LABELME_VERSION") or importlib.metadata.version("labelme")
except importlib.metadata.PackageNotFoundError:
    app_version = "0.0.0"

datas = [
    ("labelme/_config/default_config.yaml", "labelme/_config"),
    ("labelme/icons", "labelme/icons"),
    ("labelme/translate", "labelme/translate"),
]
datas += collect_data_files("osam")
datas += copy_metadata("labelme")

hiddenimports = [
    "PySide6",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "onnxruntime",
    "osam",
    "imgviz",
    "PIL",
    "ruamel.yaml",
]

a = Analysis(
    ["labelme/__main__.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

if sys.platform == "win32":
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="Labelme",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon="labelme/icons/icon.ico",
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="Labelme",
    )
elif sys.platform == "darwin":
    mac_icon = "labelme/icons/icon.icns" if os.path.exists("labelme/icons/icon.icns") else "labelme/icons/icon-macos-512.png"
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="Labelme",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=mac_icon,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="Labelme",
    )
    app = BUNDLE(
        coll,
        name="Labelme.app",
        icon=mac_icon,
        bundle_identifier="io.github.phanhai27.labelme",
        info_plist={
            "CFBundleName": "Labelme",
            "CFBundleDisplayName": "Labelme",
            "CFBundleShortVersionString": app_version,
            "CFBundleVersion": app_version,
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="Labelme",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,
        icon="labelme/icons/icon-256.png",
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name="Labelme",
    )
