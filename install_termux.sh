#!/bin/bash
# QClaw ADB Tool - Termux安装脚本

echo "======================================"
echo "  QClaw ADB Tool 安装脚本"
echo "======================================"

# 更新包管理器
echo "[1/4] 更新包管理器..."
pkg update -y && pkg upgrade -y

# 安装必要工具
echo "[2/4] 安装必要工具..."
pkg install -y python python-pip android-tools git

# 安装Python依赖
echo "[3/4] 安装Python依赖..."
pip install --upgrade pip
pip install flet

# 创建工作目录
echo "[4/4] 创建工作目录..."
mkdir -p ~/qclaw_adb
cd ~/qclaw_adb

# 下载脚本（如果存在）
if [ -f "/sdcard/qclaw_adb.py" ]; then
    cp /sdcard/qclaw_adb.py ~/qclaw_adb/
    echo "✓ 已从SD卡复制脚本"
fi

echo ""
echo "======================================"
echo "  ✓ 安装完成！"
echo "======================================"
echo ""
echo "使用方法:"
echo "  1. 将 qclaw_adb.py 复制到手机存储"
echo "  2. 在Termux中运行: python ~/qclaw_adb/qclaw_adb.py"
echo "  3. 或使用图形界面: flet run ~/qclaw_adb/qclaw_adb.py"
echo ""
echo "提示: 首次运行请授予Termux必要的权限"
echo ""
