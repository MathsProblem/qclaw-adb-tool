# QClaw ADB Tool - Termux版

## 📱 使用方法（最简单）

### 步骤1: 安装Termux

从以下任一渠道安装Termux：
- **F-Droid**: https://f-droid.org/packages/com.termux/
- **GitHub**: https://github.com/termux/termux-app/releases

> ⚠️ 不要从Google Play安装，版本过旧！

### 步骤2: 安装必要工具

打开Termux，依次执行：

```bash
# 更新包管理器
pkg update -y && pkg upgrade -y

# 安装Python和ADB工具
pkg install -y python python-pip android-tools

# 安装Flet（可选，用于图形界面）
pip install flet
```

### 步骤3: 复制脚本到手机

将 `qclaw_adb.py` 复制到手机存储：
- 数据线连接电脑 → 复制到手机内部存储根目录
- 或通过云盘/聊天软件传输

### 步骤4: 运行

**命令行模式**（推荐）：
```bash
cd /sdcard
python qclaw_adb.py
```

**图形界面模式**：
```bash
cd /sdcard
flet run qclaw_adb.py
```

---

## 🎯 功能列表

| 功能 | 命令行 | 图形界面 |
|------|--------|----------|
| 设备连接（USB/无线） | ✅ | ✅ |
| 查看设备信息 | ✅ | ✅ |
| 应用列表 | ✅ | ✅ |
| 安装/卸载应用 | ✅ | ✅ |
| 截屏 | ✅ | ✅ |
| 文件传输 | ✅ | ✅ |
| Shell命令 | ✅ | ✅ |

---

## ⚡ 快速命令

```bash
# 查看设备
adb devices

# 无线连接
adb connect 192.168.1.100:5555

# 截屏
adb shell screencap -p /sdcard/scr.png

# 安装应用
adb install app.apk

# 卸载应用
adb uninstall com.package.name

# 列出应用
adb shell pm list packages -3

# 进入Shell
adb shell
```

---

## 🔧 权限说明

Termux需要以下权限：
- **存储权限**: `termux-setup-storage`（读取脚本文件）
- **无需Root**: 基本ADB功能不需要

运行以下命令授权：
```bash
termux-setup-storage
```

---

## 📦 文件说明

```
qclaw_adb_apk/
├── qclaw_adb.py          # 主程序（复制到手机）
├── install_termux.sh      # Termux安装脚本
├── README_Termux.md       # 本说明文档
└── qclaw_adb_minimal.py   # 最小化版本（无依赖）
```

---

## 🚀 相比APK方案的优势

| 对比项 | APK构建 | Termux直接运行 |
|--------|---------|----------------|
| 难度 | 极复杂 | 简单 ✅ |
| 时间 | 30分钟+ | 5分钟 ✅ |
| 环境配置 | 大量依赖 | 自动安装 ✅ |
| 调试 | 困难 | 容易 ✅ |
| 更新 | 重新构建 | 直接改代码 ✅ |

---

## 💡 提示

1. **自控设备**: 可以在Termux中用ADB控制其他Android设备
2. **无需电脑**: 所有操作在手机上完成
3. **脚本定制**: 直接编辑Python文件添加功能

---

## ❓ 常见问题

**Q: ADB连接不上设备？**
A: 确保目标设备已开启USB调试，并授权此设备

**Q: 图形界面报错？**
A: 使用命令行模式，或检查flet是否正确安装

**Q: 提示权限不足？**
A: 运行 `termux-setup-storage` 授权存储访问

---

**作者**: QClaw  
**版本**: 1.0  
**适配**: Android 9-16
