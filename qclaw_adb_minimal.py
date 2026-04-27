#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QClaw ADB Tool - 最小化版本
仅使用Python标准库，无需安装任何依赖
"""

import subprocess
import os
import sys

def run_cmd(cmd, timeout=30):
    """执行命令"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, '', str(e)

def adb(args):
    """执行ADB命令"""
    return run_cmd(f'adb {args}')

def clear():
    """清屏"""
    os.system('clear' if os.name != 'nt' else 'cls')

def header():
    """显示标题"""
    clear()
    print("="*50)
    print("   QClaw ADB Tool v1.0 (最小化版)")
    print("="*50)
    print()

def check_adb():
    """检查ADB"""
    code, _, _ = adb('version')
    return code == 0

def show_devices():
    """显示设备"""
    code, out, _ = adb('devices -l')
    if code != 0:
        print("❌ 获取设备失败")
        return
    
    lines = out.strip().split('\n')[1:]
    if not any(l.strip() for l in lines):
        print("❌ 未检测到设备")
        return
    
    print("\n📱 已连接设备:")
    print("-"*40)
    for i, line in enumerate(lines, 1):
        if line.strip():
            parts = line.split()
            device_id = parts[0] if parts else ''
            status = parts[1] if len(parts) > 1 else ''
            if status == 'device':
                print(f"  {i}. {device_id}")
    print()

def connect_wifi():
    """无线连接"""
    ip = input("\n输入 IP:端口 (如 192.168.1.100:5555): ").strip()
    if not ip:
        return
    
    print(f"\n正在连接 {ip}...")
    code, out, _ = adb(f'connect {ip}')
    print(out.strip() if out else '❌ 连接失败')

def device_info():
    """设备信息"""
    devices = []
    code, out, _ = adb('devices')
    if code == 0:
        for line in out.strip().split('\n')[1:]:
            if 'device' in line:
                devices.append(line.split()[0])
    
    if not devices:
        print("❌ 未检测到设备")
        return
    
    device = devices[0]
    print(f"\n📱 设备: {device}")
    print("-"*40)
    
    props = [
        ('品牌', 'ro.product.brand'),
        ('型号', 'ro.product.model'),
        ('Android', 'ro.build.version.release'),
        ('SDK', 'ro.build.version.sdk'),
    ]
    
    for name, prop in props:
        _, out, _ = adb(f'-s {device} shell getprop {prop}')
        print(f"{name}: {out.strip()}")
    print()

def list_packages():
    """应用列表"""
    devices = []
    code, out, _ = adb('devices')
    if code == 0:
        for line in out.strip().split('\n')[1:]:
            if 'device' in line:
                devices.append(line.split()[0])
    
    if not devices:
        print("❌ 未检测到设备")
        return
    
    device = devices[0]
    print("\n正在获取应用列表...")
    _, out, _ = adb(f'-s {device} shell pm list packages -3')
    
    packages = [l.replace('package:', '').strip() for l in out.strip().split('\n') if l.startswith('package:')]
    
    print(f"\n📦 第三方应用 ({len(packages)}个):")
    print("-"*40)
    for i, pkg in enumerate(packages[:30], 1):
        print(f"  {i:2}. {pkg}")
    if len(packages) > 30:
        print(f"  ... 还有 {len(packages)-30} 个应用")
    print()

def screenshot():
    """截屏"""
    devices = []
    code, out, _ = adb('devices')
    if code == 0:
        for line in out.strip().split('\n')[1:]:
            if 'device' in line:
                devices.append(line.split()[0])
    
    if not devices:
        print("❌ 未检测到设备")
        return
    
    device = devices[0]
    print("\n📸 正在截屏...")
    
    adb(f'-s {device} shell screencap -p /sdcard/qclaw_scr.png')
    adb(f'-s {device} pull /sdcard/qclaw_scr.png ./qclaw_scr.png')
    
    if os.path.exists('./qclaw_scr.png'):
        print("✅ 截屏成功: ./qclaw_scr.png")
    else:
        print("❌ 截屏失败")

def install_apk():
    """安装应用"""
    path = input("\n输入APK路径: ").strip()
    if not path or not os.path.exists(path):
        print("❌ 文件不存在")
        return
    
    devices = []
    code, out, _ = adb('devices')
    if code == 0:
        for line in out.strip().split('\n')[1:]:
            if 'device' in line:
                devices.append(line.split()[0])
    
    if not devices:
        print("❌ 未检测到设备")
        return
    
    device = devices[0]
    print(f"\n正在安装 {os.path.basename(path)}...")
    _, out, _ = adb(f'-s {device} install -r "{path}"')
    print(out.strip() if out else "安装完成")

def uninstall_app():
    """卸载应用"""
    pkg = input("\n输入包名: ").strip()
    if not pkg:
        return
    
    devices = []
    code, out, _ = adb('devices')
    if code == 0:
        for line in out.strip().split('\n')[1:]:
            if 'device' in line:
                devices.append(line.split()[0])
    
    if not devices:
        print("❌ 未检测到设备")
        return
    
    device = devices[0]
    print(f"\n正在卸载 {pkg}...")
    _, out, _ = adb(f'-s {device} uninstall {pkg}')
    print(out.strip() if out else "卸载完成")

def shell_cmd():
    """执行Shell"""
    devices = []
    code, out, _ = adb('devices')
    if code == 0:
        for line in out.strip().split('\n')[1:]:
            if 'device' in line:
                devices.append(line.split()[0])
    
    if not devices:
        print("❌ 未检测到设备")
        return
    
    device = devices[0]
    
    print("\n💻 Shell模式 (输入exit退出)")
    print("-"*40)
    print("提示: 常用命令")
    print("  pm list packages    列出应用")
    print("  pm uninstall <pkg>  卸载应用")
    print("  am start -n <pkg>/<activity>  启动应用")
    print("  input text <text>   输入文本")
    print("-"*40)
    
    while True:
        try:
            cmd = input(f"\n{device}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if cmd.lower() in ('exit', 'quit'):
            break
        elif cmd:
            _, out, _ = adb(f'-s {device} shell {cmd}')
            print(out)

def main():
    """主循环"""
    if not check_adb():
        print("❌ ADB不可用！")
        print("\n请安装:")
        print("  Termux: pkg install android-tools")
        print("  Windows: 下载 Android SDK Platform Tools")
        return
    
    while True:
        header()
        print("  1. 📱 查看设备")
        print("  2. 📶 无线连接")
        print("  3. ℹ️  设备信息")
        print("  4. 📦 应用列表")
        print("  5. 📸 截屏")
        print("  6. 📲 安装应用")
        print("  7. 🗑️  卸载应用")
        print("  8. 💻 Shell命令")
        print("  0. 🚪 退出")
        print()
        print("-"*50)
        
        try:
            choice = input("  请选择 [0-8]: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        
        if choice == '0':
            print("\n再见！")
            break
        elif choice == '1':
            show_devices()
        elif choice == '2':
            connect_wifi()
        elif choice == '3':
            device_info()
        elif choice == '4':
            list_packages()
        elif choice == '5':
            screenshot()
        elif choice == '6':
            install_apk()
        elif choice == '7':
            uninstall_app()
        elif choice == '8':
            shell_cmd()
        
        if choice != '0':
            input("\n按回车继续...")

if __name__ == '__main__':
    main()
