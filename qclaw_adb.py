#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QClaw ADB Tool - 手机版ADB管理工具
适配 Termux 环境，可直接在Android手机上运行
"""

import subprocess
import os
import sys
import json
import time
from pathlib import Path

# 尝试导入UI库
try:
    import flet as ft
    HAS_FLET = True
except ImportError:
    HAS_FLET = False
    print("提示: 安装flet可获得图形界面: pip install flet")
    print("当前使用命令行模式...")

class ADBController:
    """ADB控制器"""
    
    def __init__(self):
        self.connected_devices = []
        self.adb_path = self._find_adb()
        
    def _find_adb(self):
        """查找ADB路径"""
        # Termux环境
        if os.path.exists('/data/data/com.termux'):
            adb_paths = [
                '/data/data/com.termux/files/usr/bin/adb',
                '$PREFIX/bin/adb',
            ]
            for path in adb_paths:
                if os.path.exists(os.path.expandvars(path)):
                    return os.path.expandvars(path)
        
        # 通用查找
        try:
            result = subprocess.run(['which', 'adb'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return 'adb'
    
    def _run_adb(self, args, timeout=30):
        """执行ADB命令"""
        try:
            cmd = [self.adb_path] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, '', '命令超时'
        except Exception as e:
            return -1, '', str(e)
    
    def check_adb(self):
        """检查ADB是否可用"""
        code, out, err = self._run_adb(['version'])
        return code == 0
    
    def get_devices(self):
        """获取连接的设备列表"""
        code, out, err = self._run_adb(['devices', '-l'])
        if code != 0:
            return []
        
        devices = []
        lines = out.strip().split('\n')
        for line in lines[1:]:  # 跳过标题行
            if line.strip():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    device_info = {
                        'id': parts[0],
                        'model': '',
                        'product': ''
                    }
                    # 解析设备信息
                    for part in parts[2:]:
                        if part.startswith('model:'):
                            device_info['model'] = part.split(':')[1]
                        elif part.startswith('product:'):
                            device_info['product'] = part.split(':')[1]
                    devices.append(device_info)
        
        self.connected_devices = devices
        return devices
    
    def connect_wifi(self, ip_port):
        """无线连接设备"""
        code, out, err = self._run_adb(['connect', ip_port], timeout=10)
        return code == 0, out or err
    
    def disconnect(self, device_id):
        """断开设备"""
        code, out, err = self._run_adb(['disconnect', device_id])
        return code == 0
    
    def shell(self, device_id, command):
        """执行shell命令"""
        code, out, err = self._run_adb(['-s', device_id, 'shell', command], timeout=60)
        return out if code == 0 else err
    
    def install_app(self, device_id, apk_path):
        """安装应用"""
        code, out, err = self._run_adb(['-s', device_id, 'install', '-r', apk_path], timeout=120)
        return code == 0, out or err
    
    def uninstall_app(self, device_id, package):
        """卸载应用"""
        code, out, err = self._run_adb(['-s', device_id, 'uninstall', package])
        return code == 0, out or err
    
    def list_packages(self, device_id):
        """列出已安装应用"""
        code, out, err = self._run_adb(['-s', device_id, 'shell', 'pm', 'list', 'packages', '-3'])
        if code != 0:
            return []
        packages = []
        for line in out.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line.replace('package:', '').strip())
        return packages
    
    def get_device_info(self, device_id):
        """获取设备信息"""
        info = {
            'brand': self.shell(device_id, 'getprop ro.product.brand').strip(),
            'model': self.shell(device_id, 'getprop ro.product.model').strip(),
            'android': self.shell(device_id, 'getprop ro.build.version.release').strip(),
            'sdk': self.shell(device_id, 'getprop ro.build.version.sdk').strip(),
            'serial': device_id,
        }
        return info
    
    def screenshot(self, device_id, save_path='/sdcard/screenshot.png'):
        """截屏"""
        self._run_adb(['-s', device_id, 'shell', 'screencap', '-p', save_path])
        local_path = os.path.basename(save_path)
        self._run_adb(['-s', device_id, 'pull', save_path, local_path])
        return os.path.exists(local_path), local_path
    
    def push_file(self, device_id, local_path, remote_path):
        """推送文件"""
        code, out, err = self._run_adb(['-s', device_id, 'push', local_path, remote_path])
        return code == 0, out or err
    
    def pull_file(self, device_id, remote_path, local_path):
        """拉取文件"""
        code, out, err = self._run_adb(['-s', device_id, 'pull', remote_path, local_path])
        return code == 0, local_path if code == 0 else None


# ==================== 图形界面（Flet） ====================

class ADBApp:
    """Flet图形界面"""
    
    def __init__(self):
        self.adb = ADBController()
        self.current_device = None
        
    def main(self, page: ft.Page):
        """主界面"""
        page.title = "QClaw ADB Tool"
        page.theme_mode = ft.ThemeMode.DARK
        
        # 检查ADB
        if not self.adb.check_adb():
            page.add(ft.Alert('ADB不可用，请先安装: pkg install android-tools', bgcolor='red'))
            return
        
        # 顶部状态栏
        self.status_text = ft.Text("就绪", size=12, color=ft.colors.GREY)
        
        # 设备选择
        self.device_dropdown = ft.Dropdown(
            label="选择设备",
            width=300,
            on_change=self.on_device_change
        )
        
        # 刷新设备按钮
        refresh_btn = ft.IconButton(
            icon=ft.icons.REFRESH,
            on_click=self.refresh_devices,
            tooltip="刷新设备列表"
        )
        
        # 无线连接
        self.wifi_input = ft.TextField(
            label="IP:端口",
            width=200,
            value=""
        )
        
        wifi_btn = ft.ElevatedButton(
            "连接",
            on_click=self.connect_wifi,
            icon=ft.icons.WIFI
        )
        
        # 功能按钮区
        button_grid = ft.GridView(
            expand=1,
            runs_count=3,
            max_extent=100,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
        )
        
        buttons = [
            ("📱 设备信息", self.show_device_info),
            ("📦 应用列表", self.show_packages),
            ("📸 截屏", self.take_screenshot),
            ("📁 文件管理", self.file_manager),
            ("⚙️ Shell", self.open_shell),
            ("🔄 重启设备", self.reboot_device),
        ]
        
        for text, handler in buttons:
            btn = ft.ElevatedButton(
                text,
                on_click=handler,
                width=100,
                height=80,
            )
            button_grid.controls.append(btn)
        
        # 输出区域
        self.output = ft.TextField(
            label="输出",
            multiline=True,
            read_only=True,
            min_lines=5,
            max_lines=15,
            expand=True,
            value="准备就绪..."
        )
        
        # 布局
        page.add(
            ft.Row([self.status_text], alignment=ft.MainAxisAlignment.END),
            ft.Divider(),
            ft.Text("QClaw ADB Tool", size=24, weight=ft.FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                self.device_dropdown,
                refresh_btn,
            ]),
            ft.Row([
                self.wifi_input,
                wifi_btn,
            ]),
            ft.Divider(),
            ft.Text("快捷功能", size=16),
            button_grid,
            ft.Divider(),
            self.output,
        )
        
        # 自动刷新设备
        self.refresh_devices(None)
    
    def refresh_devices(self, e):
        """刷新设备列表"""
        self.device_dropdown.options = []
        devices = self.adb.get_devices()
        
        for dev in devices:
            label = f"{dev['id']}"
            if dev['model']:
                label += f" ({dev['model']})"
            self.device_dropdown.options.append(ft.dropdown.Option(dev['id'], label))
        
        if devices:
            self.device_dropdown.value = devices[0]['id']
            self.current_device = devices[0]['id']
            self.status_text.value = f"已连接 {len(devices)} 台设备"
        else:
            self.device_dropdown.value = None
            self.current_device = None
            self.status_text.value = "未检测到设备"
        
        self.device_dropdown.update()
        self.status_text.update()
    
    def on_device_change(self, e):
        """设备选择变化"""
        self.current_device = e.control.value
    
    def connect_wifi(self, e):
        """无线连接"""
        ip_port = self.wifi_input.value.strip()
        if not ip_port:
            self.output.value = "请输入IP:端口"
            self.output.update()
            return
        
        self.output.value = f"正在连接 {ip_port}..."
        self.output.update()
        
        success, msg = self.adb.connect_wifi(ip_port)
        self.output.value = msg
        self.output.update()
        
        if success:
            self.refresh_devices(None)
    
    def show_device_info(self, e):
        """显示设备信息"""
        if not self.current_device:
            self.output.value = "请先选择设备"
            self.output.update()
            return
        
        info = self.adb.get_device_info(self.current_device)
        self.output.value = f"""设备信息
━━━━━━━━━━━━━━━━━━
品牌: {info['brand']}
型号: {info['model']}
Android版本: {info['android']}
SDK版本: {info['sdk']}
序列号: {info['serial']}
"""
        self.output.update()
    
    def show_packages(self, e):
        """显示应用列表"""
        if not self.current_device:
            self.output.value = "请先选择设备"
            self.output.update()
            return
        
        self.output.value = "正在获取应用列表..."
        self.output.update()
        
        packages = self.adb.list_packages(self.current_device)
        self.output.value = f"已安装应用 ({len(packages)}个):\n" + "\n".join(packages[:50])
        self.output.update()
    
    def take_screenshot(self, e):
        """截屏"""
        if not self.current_device:
            self.output.value = "请先选择设备"
            self.output.update()
            return
        
        self.output.value = "正在截屏..."
        self.output.update()
        
        success, path = self.adb.screenshot(self.current_device)
        self.output.value = f"截屏{'成功' if success else '失败'}\n保存至: {path}"
        self.output.update()
    
    def file_manager(self, e):
        """文件管理器"""
        self.output.value = "文件管理功能开发中..."
        self.output.update()
    
    def open_shell(self, e):
        """打开Shell"""
        self.output.value = """Shell命令模式
━━━━━━━━━━━━━━━━━━
常用命令:
• pm list packages - 列出应用
• pm uninstall <包名> - 卸载应用
• am start -n <包名>/<Activity> - 启动应用
• input text <文本> - 输入文本
• input tap <x> <y> - 点击坐标
• screencap -p /sdcard/scr.png - 截屏

请在下方输入命令执行...
"""
        self.output.update()
    
    def reboot_device(self, e):
        """重启设备"""
        if not self.current_device:
            self.output.value = "请先选择设备"
            self.output.update()
            return
        
        self.output.value = "正在重启设备..."
        self.output.update()
        
        self.adb.shell(self.current_device, 'reboot')


# ==================== 命令行界面 ====================

def cli_mode():
    """命令行交互模式"""
    adb = ADBController()
    
    print("\n" + "="*50)
    print("  QClaw ADB Tool - 命令行模式")
    print("="*50)
    
    if not adb.check_adb():
        print("❌ ADB不可用！")
        print("请安装: pkg install android-tools")
        return
    
    print("✓ ADB已就绪\n")
    
    while True:
        print("\n" + "-"*40)
        print("1. 查看设备  2. 无线连接  3. 设备信息")
        print("4. 应用列表  5. 截屏      6. Shell")
        print("7. 安装APK   8. 卸载应用  0. 退出")
        print("-"*40)
        
        try:
            choice = input("请选择: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        
        if choice == '0':
            print("再见！")
            break
        elif choice == '1':
            devices = adb.get_devices()
            if devices:
                print(f"\n已连接 {len(devices)} 台设备:")
                for i, dev in enumerate(devices, 1):
                    print(f"  {i}. {dev['id']} {dev['model']}")
            else:
                print("未检测到设备")
        
        elif choice == '2':
            ip_port = input("输入 IP:端口: ").strip()
            if ip_port:
                success, msg = adb.connect_wifi(ip_port)
                print(msg)
        
        elif choice == '3':
            devices = adb.get_devices()
            if devices:
                info = adb.get_device_info(devices[0]['id'])
                print(f"\n品牌: {info['brand']}")
                print(f"型号: {info['model']}")
                print(f"Android: {info['android']}")
            else:
                print("未检测到设备")
        
        elif choice == '4':
            devices = adb.get_devices()
            if devices:
                print("正在获取应用列表...")
                packages = adb.list_packages(devices[0]['id'])
                for pkg in packages[:20]:
                    print(f"  • {pkg}")
                if len(packages) > 20:
                    print(f"  ... 共{len(packages)}个应用")
            else:
                print("未检测到设备")
        
        elif choice == '5':
            devices = adb.get_devices()
            if devices:
                print("正在截屏...")
                success, path = adb.screenshot(devices[0]['id'])
                print(f"{'成功' if success else '失败'}: {path}")
            else:
                print("未检测到设备")
        
        elif choice == '6':
            devices = adb.get_devices()
            if devices:
                cmd = input("输入Shell命令: ").strip()
                if cmd:
                    result = adb.shell(devices[0]['id'], cmd)
                    print(result)
            else:
                print("未检测到设备")
        
        elif choice == '7':
            devices = adb.get_devices()
            if devices:
                apk_path = input("输入APK路径: ").strip()
                if apk_path and os.path.exists(apk_path):
                    success, msg = adb.install_app(devices[0]['id'], apk_path)
                    print(msg)
                else:
                    print("文件不存在")
            else:
                print("未检测到设备")
        
        elif choice == '8':
            devices = adb.get_devices()
            if devices:
                pkg = input("输入包名: ").strip()
                if pkg:
                    success, msg = adb.uninstall_app(devices[0]['id'], pkg)
                    print(msg)
            else:
                print("未检测到设备")


# ==================== 入口 ====================

if __name__ == '__main__':
    if HAS_FLET:
        # 尝试启动图形界面
        try:
            app = ADBApp()
            ft.app(target=app.main, view=ft.AppView.WEB_BROWSER)
        except Exception as e:
            print(f"图形界面启动失败: {e}")
            print("切换到命令行模式...")
            cli_mode()
    else:
        cli_mode()
