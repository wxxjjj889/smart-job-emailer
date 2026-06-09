"""一键生成分享版 EXE。运行：python build_share.py"""
import os
import shutil
import sys
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
SHARE = os.path.join(os.path.dirname(BASE), "发邮件软件_分享版")

# ---- 1. 生成干净文件夹 ----
os.makedirs(SHARE, exist_ok=True)
for item in os.listdir(SHARE):
    item_path = os.path.join(SHARE, item)
    if os.path.isdir(item_path):
        shutil.rmtree(item_path)
    else:
        os.remove(item_path)

INCLUDE = ["main.py", "test_main.py", "test_gui.py", "test_smtp.py"]
for name in INCLUDE:
    src = os.path.join(BASE, name)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(SHARE, name))
        print(f"  ✓ {name}")

os.makedirs(os.path.join(SHARE, "resumes"), exist_ok=True)
print("  ✓ resumes/ (空)")

# ---- 2. 打包成 exe ----
print("\n正在打包 exe（约需30秒）...")
import subprocess
result = subprocess.run([
    sys.executable, "-m", "PyInstaller",
    "--onefile", "--windowed", "--name", "智能投递助手", "--clean",
    "--distpath", os.path.join(SHARE, "output"),
    "--workpath", os.path.join(SHARE, "build_temp"),
    os.path.join(SHARE, "main.py"),
], capture_output=True, text=True)

if result.returncode == 0:
    exe_src = os.path.join(SHARE, "output", "智能投递助手.exe")
    exe_dst = os.path.join(os.path.dirname(BASE), "智能投递助手.exe")
    shutil.move(exe_src, exe_dst)
    print(f"  ✓ 智能投递助手.exe → {exe_dst}")
    # 清理
    shutil.rmtree(os.path.join(SHARE, "output"), ignore_errors=True)
    shutil.rmtree(os.path.join(SHARE, "build_temp"), ignore_errors=True)
    for f in os.listdir(SHARE):
        if f.endswith(".spec"):
            os.remove(os.path.join(SHARE, f))
    print("\n完成！把「智能投递助手.exe」通过微信发给好友即可。")
else:
    print("打包失败:\n", result.stderr)
