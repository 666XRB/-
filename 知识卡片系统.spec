# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['F:\\Adaogu1\\积累\\KnowledgeBaseApp\\main.py'],
    pathex=[
        'C:\\Users\\许闰博\\AppData\\Roaming\\Python\\Python312\\site-packages\\PyQt6'
    ],
    binaries=[],
    datas=[
        ('F:\\Adaogu1\\积累\\KnowledgeBaseApp\\resources\\card.ico', 'resources'),
        ('F:\\Adaogu1\\积累\\KnowledgeBaseApp\\styles\\styles.qss', 'styles'),
        ('F:\\Adaogu1\\积累\\KnowledgeBaseApp\\fonts\\msyh.ttc', 'fonts'),
        ('F:\\Adaogu1\\积累\\KnowledgeBaseApp\\fonts\\msyhbd.ttc', 'fonts'),
        ('F:\\Adaogu1\\积累\\KnowledgeBaseApp\\fonts\\msyhl.ttc', 'fonts'),
        ('F:\\Adaogu1\\积累\\KnowledgeBaseApp\\utils\\export_pdf.py', 'utils')  # 添加PDF导出模块
    ],
    hiddenimports=[
        'PyQt6.QtWidgets',
        'PyQt6.QtGui',
        'PyQt6.QtCore',
        'PyQt6.QtNetwork',
        'fpdf',
        'fpdf.enums',
        'datetime',
        'PIL',
        'winreg',
        'cryptography',  # 新增
        'email.mime.multipart',  # 新增
        'email.mime.text',  # 新增
        'json',  # 新增
        'smtplib'  # 新增
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'numpy'],  # 不再排除PIL
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='知识卡片系统',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    version='version_info.txt',  # 改为引用版本信息文件
    uac_admin=False,  # 修改这里，从True改为False
    icon=['F:\\Adaogu1\\积累\\KnowledgeBaseApp\\resources\\card.ico'],
)
