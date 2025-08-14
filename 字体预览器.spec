# -*- mode: python ; coding: utf-8 -*-

import sys
import os
import platform

# --- [新增] 图标合并逻辑 ---
# 这个函数会在打包开始时被调用
def merge_icons():
    # 只在 Windows 系统上执行此操作
    if platform.system() != "Windows":
        # 在非 Windows 系统上，我们可以选择一个 PNG 作为备用图标
        # 或者直接返回 None
        if os.path.exists('assets/IMG.png'):
            return 'assets/IMG.png' # Linux/macOS 可以使用 png
        return None

    # 定义源图标文件的路径
    icon_paths = [
        'assets/IMG_16.ico',
        'assets/IMG_32.ico',
        'assets.IMG_256.ico' # 确保文件名正确
    ]
    
    # 检查所有源图标是否存在
    for path in icon_paths:
        if not os.path.exists(path):
            print(f"警告：图标文件 {path} 不存在，跳过合并。")
            # 如果缺少关键图标，可以选择一个存在的作为备用
            return 'assets/IMG_256.ico' if os.path.exists('assets/IMG_256.ico') else None

    # 定义合并后输出的图标文件名
    merged_icon_path = 'merged_icon.ico'
    
    # 构建 Windows 的 copy 命令
    # 格式: copy /b file1.ico + file2.ico + ... output.ico
    # /b 表示以二进制模式复制
    command = f'copy /b {" + ".join(icon_paths)} {merged_icon_path}'
    
    print(f"正在执行图标合并命令: {command}")
    
    # 执行命令
    result = os.system(command)
    
    if result == 0:
        print(f"图标成功合并到 {merged_icon_path}")
        return merged_icon_path
    else:
        print(f"警告：图标合并失败。将使用单个图标作为备用。")
        return 'assets/IMG_256.ico' if os.path.exists('assets/IMG_256.ico') else None

# --- 调用图标合并函数 ---
final_icon_path = merge_icons()


# --- 配置区 ---
# 定义要捆绑到程序内部的数据文件和文件夹
datas_to_include = [
    ('assets', 'assets'),
    ('fonts', 'default_fonts')
]

# 定义要捆绑的二进制文件
binaries_to_include = []
if sys.platform == 'linux':
    # 将 'lib' 目录下的 so 文件，放到程序包内的 'lib' 目录
    binaries_to_include.append(('lib/libfcitx5platforminputcontextplugin.so', 'lib'))

# 定义隐藏依赖
hidden_imports = ['PyQt5.sip']

a = Analysis(
    ['1.py'],
    pathex=[],
    binaries=binaries_to_include,
    datas=datas_to_include,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='字体预览器',
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
    icon=final_icon_path
)
