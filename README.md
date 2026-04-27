# QClaw ADB工具箱 - Android版

## 简介

这是mi.py的Android版本,使用Flet框架开发。支持Android 9~16。

### 主要功能

1. **设备仪表盘** - 显示CPU/内存/电池/存储状态
2. **应用管理** - 冻结/解冻/卸载应用
3. **文件管理** - 浏览设备文件系统
4. **工具箱** - 截屏/录屏/亮度调节/快捷开关等
5. **设备信息** - 查看完整设备信息

### 与Windows版的区别

- ✅ 保留了核心ADB功能
- ✅ 适配了Android手机界面
- ❌ 移除了远程控制(scrcpy)功能
- ❌ 移除了Windows特有的DWM窗口效果
- ✅ 支持直接执行shell命令(无需adb命令)

## 构建APK

### 方法一: 使用GitHub Actions (推荐)

1. 将此文件夹上传到GitHub仓库
2. 添加`.github/workflows/build.yml`:

```yaml
name: Build APK
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install flet
          pip install pyinstaller
      
      - name: Build APK
        run: |
          flet build apk
```

3. 等待构建完成后下载APK

### 方法二: 本地构建 (需要Linux环境)

#### 环境要求

- Ubuntu 20.04+ (或WSL2)
- Python 3.10+
- 至少8GB RAM
- 30GB+ 磁盘空间

#### 构建步骤

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev automake

# 2. 安装Flet
pip3 install flet

# 3. 克隆项目
cd Desktop/qclaw_adb_apk

# 4. 构建APK
flet build apk

# 5. APK位置: build/qclaw_adb.apk
```

### 方法三: 使用Docker

```bash
# 构建Docker镜像
docker build -t flet-builder .

# 运行构建
docker run -v $(pwd):/app flet-builder

# APK会生成在当前目录
```

### 方法四: 使用在线构建服务

1. **FlutLab.io** (免费)
   - 访问 https://flutlab.io
   - 上传项目文件
   - 点击Build APK

2. **Codemagic** (免费额度)
   - 连接GitHub仓库
   - 配置Flutter构建
   - 自动构建APK

## 权限说明

应用需要以下权限:

- `INTERNET` - 网络访问
- `ACCESS_WIFI_STATE` - WiFi状态
- `ACCESS_NETWORK_STATE` - 网络状态  
- `WRITE_EXTERNAL_STORAGE` - 文件写入
- `READ_EXTERNAL_STORAGE` - 文件读取
- `CAMERA` - 截屏/录屏

## 注意事项

1. **部分功能需要ROOT权限**,如:
   - 卸载系统应用
   - 修改系统设置
   - 访问受保护目录

2. **Android 11+** 需要:
   - 开启"允许修改系统设置"权限
   - 手动授予存储权限

3. **应用签名**: 构建时会自动生成调试签名,发布时请使用正式签名

## 已知问题

- 部分华为/小米设备可能需要额外权限
- Android 14+ 部分shell命令受限
- 录屏最长30秒(系统限制)

## 技术栈

- **框架**: Flet (基于Flutter)
- **语言**: Python 3.11
- **最低API**: 28 (Android 9)
- **目标API**: 34 (Android 14)

## 许可证

MIT License
