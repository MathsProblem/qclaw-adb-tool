#!/usr/bin/env python3
"""
QClaw ADB APK 构建助手
帮助用户快速构建Android APK
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

class BuildHelper:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.apk_name = "qclaw_adb"
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def show_banner(self):
        print("""
╔═══════════════════════════════════════════════════╗
║     QClaw ADB工具箱 - Android版 构建助手        ║
║         支持 Android 9~16 (API 28-34)            ║
╚═══════════════════════════════════════════════════╝
""")
    
    def check_environment(self):
        """检查构建环境"""
        print("\n📋 检查构建环境...\n")
        
        # 检查Python
        print(f"✓ Python版本: {sys.version}")
        
        # 检查pip
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "--version"],
                                  capture_output=True, text=True)
            print(f"✓ Pip版本: {result.stdout.split()[1] if result.returncode == 0 else '未安装'}")
        except:
            print("✗ Pip未安装")
        
        # 检查Flet
        try:
            import flet
            print(f"✓ Flet版本: {flet.__version__}")
        except ImportError:
            print("✗ Flet未安装 (运行'pip install flet'安装)")
        
        # 检查Git (用于GitHub Actions)
        try:
            result = subprocess.run(["git", "--version"], capture_output=True, text=True)
            print(f"✓ Git: {result.stdout.strip()}")
        except:
            print("⚠ Git未安装 (可选,用于GitHub自动构建)")
        
        # 操作系统
        print(f"✓ 操作系统: {platform.system()} {platform.release()}")
        
        print()
    
    def install_flet(self):
        """安装Flet"""
        print("\n📦 正在安装Flet...\n")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "flet"], check=True)
            print("\n✓ Flet安装成功!\n")
        except subprocess.CalledProcessError:
            print("\n✗ Flet安装失败,请手动运行: pip install flet\n")
    
    def preview_app(self):
        """预览应用"""
        print("\n🚀 启动应用预览...\n")
        print("(提示: 在Windows上预览会显示桌面版界面)")
        print("(实际APK会在Android上以移动端界面运行)\n")
        
        try:
            subprocess.run([sys.executable, "main.py"], cwd=self.project_dir)
        except KeyboardInterrupt:
            print("\n\n应用已关闭")
    
    def show_build_options(self):
        """显示构建选项"""
        print("\n" + "═"*50)
        print("📱 APK构建选项")
        print("═"*50)
        print()
        print("方法一: GitHub Actions自动构建 (推荐)")
        print("  1. 上传项目到GitHub")
        print("  2. GitHub自动构建")
        print("  3. 下载APK")
        print()
        print("方法二: WSL2本地构建")
        print("  1. 启用WSL2: wsl --install -d Ubuntu-22.04")
        print("  2. 安装依赖: sudo apt install ...")
        print("  3. 构建APK: flet build apk")
        print()
        print("方法三: 在线构建服务")
        print("  1. FlutLab.io (免费)")
        print("  2. CodeMagic.io (免费额度)")
        print()
        print("方法四: 使用buildozer (传统)")
        print("  buildozer android debug")
        print()
    
    def create_github_readme(self):
        """创建GitHub README"""
        readme = f"""# {self.apk_name}

## 自动构建APK

本项目使用GitHub Actions自动构建Android APK。

### 下载APK

1. 点击上方的"Actions"标签
2. 选择最新的构建
3. 在"Artifacts"中下载APK
4. 安装到Android设备

### 本地构建

```bash
# 安装Flet
pip install flet

# 构建APK
flet build apk
```

### 支持的Android版本

- Android 9 (API 28)
- Android 10 (API 29)
- Android 11 (API 30)
- Android 12 (API 31)
- Android 13 (API 33)
- Android 14 (API 34)

### 功能

- 📱 设备信息查看
- 📦 应用管理 (冻结/解冻/卸载)
- 📁 文件浏览器
- 🛠️ 系统工具箱
- 🔧 ADB命令执行
"""
        readme_path = self.project_dir / "GITHUB_README.md"
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme)
        print(f"\n✓ 已创建: {readme_path}")
    
    def run(self):
        """运行主菜单"""
        while True:
            self.clear_screen()
            self.show_banner()
            
            print("请选择操作:\n")
            print("  [1] 检查构建环境")
            print("  [2] 安装Flet依赖")
            print("  [3] 预览应用 (Windows)")
            print("  [4] 查看构建选项")
            print("  [5] 创建GitHub上传包")
            print("  [6] 查看项目信息")
            print("  [0] 退出")
            print()
            
            choice = input("请输入选项: ").strip()
            
            if choice == '1':
                self.check_environment()
                input("\n按回车继续...")
            elif choice == '2':
                self.install_flet()
                input("\n按回车继续...")
            elif choice == '3':
                self.preview_app()
                input("\n按回车继续...")
            elif choice == '4':
                self.show_build_options()
                input("\n按回车继续...")
            elif choice == '5':
                self.create_github_readme()
                input("\n按回车继续...")
            elif choice == '6':
                print("\n项目信息:")
                print(f"  项目目录: {self.project_dir}")
                print(f"  主程序: main.py")
                print(f"  APK名称: {self.apk_name}.apk")
                input("\n按回车继续...")
            elif choice == '0':
                print("\n感谢使用!\n")
                break
            else:
                print("\n无效选项,请重新输入")
                input("\n按回车继续...")

if __name__ == "__main__":
    try:
        helper = BuildHelper()
        helper.run()
    except KeyboardInterrupt:
        print("\n\n已退出")
