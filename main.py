"""
QClaw ADB Tool - Android版本
支持Android 9~16
使用Flet框架开发
"""

import flet as ft
import subprocess
import os
import re
import json
import threading
import time
from pathlib import Path

# ================= 配置 =================
class Config:
    APP_NAME = "QClaw ADB工具箱"
    VERSION = "1.0.0"
    SETTINGS_FILE = "qclaw_adb_settings.json"
    
    # 颜色主题
    PRIMARY = "#4f46e5"
    PRIMARY_LIGHT = "#6366f1"
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#0ea5e9"
    
    # 内置包名
    APPSTORE_PKG = "com.iflytek.appshop"
    MDM_PKG = "com.iflytek.ebg.aistudy.mdm"

# ================= ADB核心（Android版本）=================
class ADBTool:
    @staticmethod
    def run_shell_command(cmd: str, timeout: int = 30) -> tuple:
        """在Android上直接执行shell命令"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                encoding='utf-8',
                errors='ignore'
            )
            output = f"{result.stdout.strip()}\n{result.stderr.strip()}".strip()
            return output, result.returncode
        except subprocess.TimeoutExpired:
            return "命令超时", -1
        except Exception as e:
            return f"执行失败: {str(e)}", -1
    
    @staticmethod
    def check_root() -> bool:
        """检查是否有root权限"""
        out, code = ADBTool.run_shell_command("su -c 'id'")
        return code == 0 and "uid=0" in out
    
    @staticmethod
    def get_device_info() -> dict:
        """获取设备信息"""
        info = {}
        
        # 基本信息
        props = {
            "设备型号": "ro.product.model",
            "设备厂商": "ro.product.manufacturer",
            "Android版本": "ro.build.version.release",
            "SDK版本": "ro.build.version.sdk",
            "设备名称": "ro.product.name",
            "系统版本": "ro.build.display.id",
            "安全补丁": "ro.build.version.security_patch",
            "内核版本": "ro.kernel.qemu",
        }
        
        for name, prop in props.items():
            out, _ = ADBTool.run_shell_command(f"getprop {prop}")
            info[name] = out.strip() if out.strip() else "未知"
        
        # 屏幕分辨率
        out, _ = ADBTool.run_shell_command("wm size")
        info["屏幕分辨率"] = out.replace("Physical size: ", "").strip()
        
        # DPI
        out, _ = ADBTool.run_shell_command("wm density")
        info["屏幕DPI"] = out.replace("Physical density: ", "").strip()
        
        # 电池电量
        out, _ = ADBTool.run_shell_command("dumpsys battery | grep level")
        if "level:" in out:
            info["电池电量"] = out.split(":")[1].strip() + "%"
        
        return info
    
    @staticmethod
    def get_cpu_usage() -> int:
        """获取CPU使用率"""
        out, _ = ADBTool.run_shell_command("top -n 1 | grep 'CPU'")
        m = re.search(r'(\d+(?:\.\d+)?)\s*%?\s*user', out)
        if m:
            return int(float(m.group(1)))
        return 0
    
    @staticmethod
    def get_memory_usage() -> int:
        """获取内存使用率"""
        out, _ = ADBTool.run_shell_command("cat /proc/meminfo")
        total = avail = 0
        for line in out.splitlines():
            if "MemTotal:" in line:
                total = int(line.split()[1])
            elif "MemAvailable:" in line:
                avail = int(line.split()[1])
        if total:
            return int((total - avail) / total * 100)
        return 0
    
    @staticmethod
    def get_storage_usage() -> tuple:
        """获取存储使用情况"""
        out, _ = ADBTool.run_shell_command("df /data")
        for line in out.splitlines():
            if '/data' in line and not line.startswith('Filesystem'):
                parts = line.split()
                if len(parts) >= 5:
                    return parts[1], parts[2], parts[4]
        return "N/A", "N/A", "N/A"
    
    @staticmethod
    def list_packages(show_all: bool = False) -> list:
        """列出已安装的应用"""
        cmd = "pm list packages"
        if show_all:
            cmd += " -u"
        out, _ = ADBTool.run_shell_command(cmd)
        return re.findall(r"package:(.+?)(?:\s|$)", out)
    
    @staticmethod
    def get_disabled_packages() -> list:
        """获取已冻结的应用"""
        out, _ = ADBTool.run_shell_command("pm list packages -d")
        return re.findall(r"package:(.+?)(?:\s|$)", out)
    
    @staticmethod
    def disable_package(pkg: str) -> tuple:
        """冻结应用"""
        out, code = ADBTool.run_shell_command(f"pm disable-user --user 0 {pkg}")
        return out, code == 0
    
    @staticmethod
    def enable_package(pkg: str) -> tuple:
        """解冻应用"""
        out, code = ADBTool.run_shell_command(f"pm enable {pkg}")
        return out, code == 0
    
    @staticmethod
    def uninstall_package(pkg: str) -> tuple:
        """卸载应用"""
        out, code = ADBTool.run_shell_command(f"pm uninstall --user 0 {pkg}")
        return out, code == 0 and "Success" in out
    
    @staticmethod
    def clear_package_data(pkg: str) -> tuple:
        """清除应用数据"""
        out, code = ADBTool.run_shell_command(f"pm clear {pkg}")
        return out, code == 0 and "Success" in out
    
    @staticmethod
    def force_stop_package(pkg: str) -> bool:
        """强制停止应用"""
        _, code = ADBTool.run_shell_command(f"am force-stop {pkg}")
        return code == 0
    
    @staticmethod
    def get_package_info(pkg: str) -> dict:
        """获取应用详情"""
        info = {"包名": pkg}
        
        # 版本名
        out, _ = ADBTool.run_shell_command(f"dumpsys package {pkg} | grep versionName")
        m = re.search(r'versionName=([^\s]+)', out)
        if m:
            info["版本"] = m.group(1)
        
        # 数据路径
        out, _ = ADBTool.run_shell_command(f"pm path {pkg}")
        if out.startswith("package:"):
            info["APK路径"] = out[8:].strip()
        
        return info
    
    @staticmethod
    def get_package_size(pkg: str) -> str:
        """获取应用大小"""
        out, _ = ADBTool.run_shell_command(f"du -sh /data/data/{pkg} 2>/dev/null || echo 'N/A'")
        return out.strip()
    
    @staticmethod
    def list_files(path: str = "/sdcard") -> list:
        """列出文件"""
        out, _ = ADBTool.run_shell_command(f"ls -la '{path}' 2>/dev/null")
        files = []
        for line in out.splitlines():
            if not line.strip() or line.startswith("total"):
                continue
            parts = line.split(None, 7)
            if len(parts) >= 8:
                perms = parts[0]
                size = parts[3]
                name = parts[7]
                is_dir = perms.startswith('d')
                files.append({
                    "name": name,
                    "size": size,
                    "perms": perms,
                    "is_dir": is_dir
                })
        return files
    
    @staticmethod
    def screenshot(save_path: str = "/sdcard/screenshot.png") -> bool:
        """截屏"""
        _, code = ADBTool.run_shell_command(f"screencap -p {save_path}")
        return code == 0
    
    @staticmethod
    def start_recording(path: str = "/sdcard/record.mp4", duration: int = 30):
        """开始录屏"""
        return threading.Thread(
            target=lambda: ADBTool.run_shell_command(
                f"screenrecord --time-limit {duration} {path}",
                timeout=duration + 5
            ),
            daemon=True
        )
    
    @staticmethod
    def set_brightness(value: int):
        """设置亮度 (0-255)"""
        ADBTool.run_shell_command(f"settings put system screen_brightness {value}")
    
    @staticmethod
    def get_brightness() -> int:
        """获取当前亮度"""
        out, _ = ADBTool.run_shell_command("settings get system screen_brightness")
        try:
            return int(out.strip())
        except:
            return 128
    
    @staticmethod
    def set_screen_timeout(seconds: int):
        """设置屏幕超时"""
        ADBTool.run_shell_command(f"settings put system screen_off_timeout {seconds * 1000}")
    
    @staticmethod
    def send_keyevent(keycode: int):
        """发送按键事件"""
        ADBTool.run_shell_command(f"input keyevent {keycode}")
    
    @staticmethod
    def send_tap(x: int, y: int):
        """发送点击事件"""
        ADBTool.run_shell_command(f"input tap {x} {y}")
    
    @staticmethod
    def send_swipe(x1: int, y1: int, x2: int, y2: int, duration: int = 300):
        """发送滑动事件"""
        ADBTool.run_shell_command(f"input swipe {x1} {y1} {x2} {y2} {duration}")
    
    @staticmethod
    def send_text(text: str):
        """发送文本"""
        # 转义特殊字符
        text = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        ADBTool.run_shell_command(f"input text '{text}'")
    
    @staticmethod
    def wifi_enable(enable: bool = True):
        """开关WiFi"""
        action = "enable" if enable else "disable"
        ADBTool.run_shell_command(f"svc wifi {action}")
    
    @staticmethod
    def bluetooth_enable(enable: bool = True):
        """开关蓝牙 (需要root)"""
        action = "enable" if enable else "disable"
        ADBTool.run_shell_command(f"service call bluetooth_manager 6 i32 {0 if enable else 1}")
    
    @staticmethod
    def airplane_mode_enable(enable: bool = True):
        """开关飞行模式"""
        value = "1" if enable else "0"
        ADBTool.run_shell_command(f"settings put global airplane_mode_on {value}")
        ADBTool.run_shell_command("am broadcast -a android.intent.action.AIRPLANE_MODE")
    
    @staticmethod
    def flashlight_enable(enable: bool = True):
        """开关手电筒"""
        action = "enableTorch" if enable else "disableTorch"
        ADBTool.run_shell_command(f"input keyevent {action}")
    
    @staticmethod
    def get_battery_info() -> dict:
        """获取电池信息"""
        info = {}
        out, _ = ADBTool.run_shell_command("dumpsys battery")
        for line in out.splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key == "level":
                    info["电量"] = val + "%"
                elif key == "temperature":
                    try:
                        temp = float(val) / 10
                        info["温度"] = f"{temp}°C"
                    except:
                        pass
                elif key == "voltage":
                    try:
                        volt = float(val) / 1000
                        info["电压"] = f"{volt:.2f}V"
                    except:
                        pass
                elif key == "health":
                    health_map = {"1": "未知", "2": "良好", "3": "过热", "4": "损坏", "5": "过压", "7": "冷冻"}
                    info["健康"] = health_map.get(val, val)
                elif key == "status":
                    status_map = {"1": "未知", "2": "充电中", "3": "放电", "4": "未充电", "5": "充满"}
                    info["状态"] = status_map.get(val, val)
        return info
    
    @staticmethod
    def get_network_info() -> dict:
        """获取网络信息"""
        info = {}
        
        # WiFi状态
        out, _ = ADBTool.run_shell_command("dumpsys wifi | grep 'mWifiInfo'")
        m = re.search(r'SSID: "([^"]+)"', out)
        if m:
            info["WiFi名称"] = m.group(1)
        m = re.search(r'ipaddr: ([\d.]+)', out)
        if m:
            info["IP地址"] = m.group(1)
        
        # 网络类型
        out, _ = ADBTool.run_shell_command("getprop gsm.network.type")
        if out.strip():
            info["网络类型"] = out.strip()
        
        return info
    
    @staticmethod
    def toast(message: str):
        """显示Toast消息"""
        ADBTool.run_shell_command(f"am broadcast -a android.intent.action.MAIN --es msg '{message}' -n com.android.systemui/.toast.ToastService")

# ================= 主应用 =================
class QClawADBApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.current_tab = 0
        self.settings = self.load_settings()
        
        # 初始化页面
        self.setup_page()
        self.create_ui()
        
    def setup_page(self):
        """设置页面基本属性"""
        self.page.title = Config.APP_NAME
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.primary_color = Config.PRIMARY
        self.page.window_width = 400
        self.page.window_height = 800
        
        # 如果是Android设备
        if hasattr(self.page, 'window_width'):
            try:
                self.page.window_width = None  # 全屏
                self.page.window_height = None
            except:
                pass
    
    def load_settings(self) -> dict:
        """加载设置"""
        try:
            if os.path.exists(Config.SETTINGS_FILE):
                with open(Config.SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_settings(self):
        """保存设置"""
        try:
            with open(Config.SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def show_snackbar(self, message: str, color: str = Config.PRIMARY):
        """显示提示消息"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white"),
            bgcolor=color
        )
        self.page.snack_bar.open = True
        self.page.update()
    
    def create_ui(self):
        """创建主界面"""
        # 底部导航栏
        self.nav_bar = ft.NavigationBar(
            destinations=[
                ft.NavigationDestination(icon=ft.icons.HOME, label="主页"),
                ft.NavigationDestination(icon=ft.icons.APPS, label="应用"),
                ft.NavigationDestination(icon=ft.icons.FOLDER, label="文件"),
                ft.NavigationDestination(icon=ft.icons.SETTINGS, label="工具"),
                ft.NavigationDestination(icon=ft.icons.INFO, label="信息"),
            ],
            on_change=self.on_nav_change,
            selected_index=0,
        )
        
        # 主内容区域
        self.content_area = ft.Container(
            content=self.get_home_tab(),
            expand=True,
            padding=10,
        )
        
        # 页面布局
        self.page.add(
            ft.Column(
                [
                    self.content_area,
                    self.nav_bar,
                ],
                expand=True,
            )
        )
    
    def on_nav_change(self, e):
        """导航栏切换事件"""
        self.current_tab = e.control.selected_index
        tabs = [
            self.get_home_tab,
            self.get_app_tab,
            self.get_file_tab,
            self.get_tool_tab,
            self.get_info_tab,
        ]
        self.content_area.content = tabs[self.current_tab]()
        self.page.update()
    
    # ================= 主页标签 =================
    def get_home_tab(self):
        """主页：仪表盘"""
        # 获取设备信息
        device_info = ADBTool.get_device_info()
        
        # 获取资源使用情况
        cpu = ADBTool.get_cpu_usage()
        mem = ADBTool.get_memory_usage()
        storage_total, storage_used, storage_pct = ADBTool.get_storage_usage()
        battery = ADBTool.get_battery_info()
        
        return ft.Column(
            [
                # 标题
                ft.Container(
                    content=ft.Text(
                        f"欢迎使用 {Config.APP_NAME}",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=Config.PRIMARY,
                    ),
                    padding=20,
                ),
                
                # 设备信息卡片
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.ListTile(
                                    leading=ft.Icon(ft.icons.PHONE_ANDROID, color=Config.PRIMARY),
                                    title=ft.Text(f"{device_info.get('设备型号', '未知')}", size=18, weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(f"Android {device_info.get('Android版本', '?')}"),
                                ),
                            ]
                        ),
                        padding=10,
                    ),
                ),
                
                ft.Divider(),
                
                # 资源使用情况
                ft.Text("系统状态", size=18, weight=ft.FontWeight.BOLD),
                
                # CPU使用率
                self.create_progress_card("CPU使用率", cpu, Config.PRIMARY),
                
                # 内存使用率
                self.create_progress_card("内存占用", mem, Config.SUCCESS),
                
                # 存储使用
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"存储空间", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(f"总容量: {storage_total} | 已用: {storage_used} ({storage_pct})", size=12),
                            ],
                            spacing=5,
                        ),
                        padding=15,
                    ),
                ),
                
                # 电池信息
                ft.Card(
                    content=ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(f"🔋 电池信息", size=14, weight=ft.FontWeight.BOLD),
                                ft.Text(f"电量: {battery.get('电量', 'N/A')} | 温度: {battery.get('温度', 'N/A')}", size=12),
                                ft.Text(f"健康: {battery.get('健康', 'N/A')} | 状态: {battery.get('状态', 'N/A')}", size=12),
                            ],
                            spacing=5,
                        ),
                        padding=15,
                    ),
                ),
                
                # 快捷操作按钮
                ft.Divider(),
                ft.Text("快捷操作", size=18, weight=ft.FontWeight.BOLD),
                
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "截屏",
                            icon=ft.icons.SCREENSHOT,
                            on_click=lambda e: self.quick_screenshot(),
                            color=Config.PRIMARY,
                        ),
                        ft.ElevatedButton(
                            "亮屏",
                            icon=ft.icons.LIGHT_MODE,
                            on_click=lambda e: ADBTool.send_keyevent(224),
                            color=Config.WARNING,
                        ),
                        ft.ElevatedButton(
                            "熄屏",
                            icon=ft.icons.DARK_MODE,
                            on_click=lambda e: ADBTool.send_keyevent(26),
                            color=Config.INFO,
                        ),
                    ],
                    wrap=True,
                ),
                
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "WiFi开关",
                            icon=ft.icons.WIFI,
                            on_click=lambda e: self.toggle_wifi(),
                            color=Config.SUCCESS,
                        ),
                        ft.ElevatedButton(
                            "飞行模式",
                            icon=ft.icons.AIRPLANEMODE_ON,
                            on_click=lambda e: self.toggle_airplane(),
                            color=Config.WARNING,
                        ),
                        ft.ElevatedButton(
                            "手电筒",
                            icon=ft.icons.FLASH_ON,
                            on_click=lambda e: self.toggle_flashlight(),
                            color=Config.ERROR,
                        ),
                    ],
                    wrap=True,
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
        )
    
    def create_progress_card(self, title: str, value: int, color: str) -> ft.Control:
        """创建进度卡片"""
        return ft.Card(
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"{title}: {value}%", size=14, weight=ft.FontWeight.BOLD),
                        ft.ProgressBar(value=value / 100, color=color, height=8),
                    ],
                    spacing=8,
                ),
                padding=15,
            ),
        )
    
    def quick_screenshot(self):
        """快速截屏"""
        if ADBTool.screenshot():
            self.show_snackbar("截屏已保存到 /sdcard/screenshot.png", Config.SUCCESS)
        else:
            self.show_snackbar("截屏失败", Config.ERROR)
    
    def toggle_wifi(self):
        """切换WiFi"""
        ADBTool.wifi_enable()
        self.show_snackbar("已切换WiFi状态", Config.INFO)
    
    def toggle_airplane(self):
        """切换飞行模式"""
        ADBTool.airplane_mode_enable()
        self.show_snackbar("已切换飞行模式", Config.WARNING)
    
    def toggle_flashlight(self):
        """切换手电筒"""
        ADBTool.flashlight_enable()
        self.show_snackbar("已切换手电筒", Config.WARNING)
    
    # ================= 应用管理标签 =================
    def get_app_tab(self):
        """应用管理"""
        # 获取已安装应用列表
        packages = ADBTool.list_packages()
        
        # 搜索框
        search_field = ft.TextField(
            hint_text="搜索应用包名...",
            prefix_icon=ft.icons.SEARCH,
            on_change=lambda e: self.filter_packages(e, package_list),
            expand=True,
        )
        
        # 应用列表
        package_list = ft.ListView(
            controls=[self.create_package_item(pkg) for pkg in sorted(packages)],
            expand=True,
        )
        
        return ft.Column(
            [
                ft.Container(
                    content=ft.Text("应用管理", size=24, weight=ft.FontWeight.BOLD),
                    padding=20,
                ),
                
                # 快捷操作
                ft.Row(
                    [
                        ft.ElevatedButton(
                            "冻结讯飞应用商店",
                            on_click=lambda e: self.disable_app(Config.APPSTORE_PKG),
                            color=Config.ERROR,
                            icon=ft.icons.DELETE,
                        ),
                        ft.ElevatedButton(
                            "冻结MDM",
                            on_click=lambda e: self.disable_app(Config.MDM_PKG),
                            color=Config.ERROR,
                            icon=ft.icons.DELETE,
                        ),
                    ],
                ),
                
                ft.Divider(),
                
                # 搜索框
                ft.Container(content=search_field, padding=10),
                
                # 应用列表
                ft.Container(content=package_list, expand=True),
            ],
            expand=True,
        )
    
    def create_package_item(self, pkg: str) -> ft.Control:
        """创建应用列表项"""
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.icons.APPS, color=Config.PRIMARY),
                        ft.Text(pkg, size=12, expand=True),
                        ft.IconButton(
                            icon=ft.icons.PAUSE_CIRCLE,
                            icon_color=Config.WARNING,
                            tooltip="冻结",
                            on_click=lambda e, p=pkg: self.disable_app(p),
                        ),
                        ft.IconButton(
                            icon=ft.icons.PLAY_CIRCLE,
                            icon_color=Config.SUCCESS,
                            tooltip="解冻",
                            on_click=lambda e, p=pkg: self.enable_app(p),
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE_FOREVER,
                            icon_color=Config.ERROR,
                            tooltip="卸载",
                            on_click=lambda e, p=pkg: self.uninstall_app(p),
                        ),
                    ],
                ),
                padding=10,
            ),
        )
    
    def filter_packages(self, e, list_control: ft.ListView):
        """过滤应用列表"""
        keyword = e.control.value.lower()
        packages = ADBTool.list_packages()
        filtered = [pkg for pkg in packages if keyword in pkg.lower()]
        list_control.controls = [self.create_package_item(pkg) for pkg in sorted(filtered)]
        self.page.update()
    
    def disable_app(self, pkg: str):
        """冻结应用"""
        out, ok = ADBTool.disable_package(pkg)
        if ok:
            self.show_snackbar(f"已冻结 {pkg}", Config.SUCCESS)
        else:
            self.show_snackbar(f"冻结失败: {out[:50]}", Config.ERROR)
    
    def enable_app(self, pkg: str):
        """解冻应用"""
        out, ok = ADBTool.enable_package(pkg)
        if ok:
            self.show_snackbar(f"已解冻 {pkg}", Config.SUCCESS)
        else:
            self.show_snackbar(f"解冻失败: {out[:50]}", Config.ERROR)
    
    def uninstall_app(self, pkg: str):
        """卸载应用"""
        # 显示确认对话框
        def on_confirm(e):
            ADBTool.uninstall_package(pkg)
            self.show_snackbar(f"已卸载 {pkg}", Config.SUCCESS)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("确认卸载"),
            content=ft.Text(f"确定要卸载 {pkg} 吗？"),
            actions=[
                ft.TextButton("取消", on_click=lambda e: setattr(self.page.dialog, 'open', False)),
                ft.TextButton("确认", on_click=on_confirm),
            ],
        )
        self.page.dialog.open = True
        self.page.update()
    
    # ================= 文件管理标签 =================
    def get_file_tab(self):
        """文件管理"""
        self.current_path = "/sdcard"
        
        # 路径显示
        self.path_text = ft.Text(self.current_path, size=14, weight=ft.FontWeight.BOLD)
        
        # 文件列表
        self.file_list = ft.ListView(expand=True)
        self.refresh_files()
        
        return ft.Column(
            [
                ft.Container(
                    content=ft.Text("文件管理", size=24, weight=ft.FontWeight.BOLD),
                    padding=20,
                ),
                
                # 工具栏
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            on_click=lambda e: self.go_up(),
                        ),
                        ft.IconButton(
                            icon=ft.icons.REFRESH,
                            on_click=lambda e: self.refresh_files(),
                        ),
                        self.path_text,
                    ],
                ),
                
                ft.Divider(),
                
                # 文件列表
                self.file_list,
            ],
            expand=True,
        )
    
    def refresh_files(self):
        """刷新文件列表"""
        files = ADBTool.list_files(self.current_path)
        self.file_list.controls = [
            self.create_file_item(f) for f in sorted(files, key=lambda x: (not x['is_dir'], x['name'].lower()))
        ]
        self.path_text.value = self.current_path
        self.page.update()
    
    def create_file_item(self, file_info: dict) -> ft.Control:
        """创建文件列表项"""
        icon = ft.icons.FOLDER if file_info['is_dir'] else ft.icons.INSERT_DRIVE_FILE
        return ft.Card(
            content=ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(icon, color=Config.PRIMARY if file_info['is_dir'] else Config.TEXT),
                        ft.Column(
                            [
                                ft.Text(file_info['name'], size=12),
                                ft.Text(file_info['size'], size=10, color=Config.TEXT),
                            ],
                            expand=True,
                        ),
                    ],
                ),
                padding=10,
                on_click=lambda e, f=file_info: self.on_file_click(f),
            ),
        )
    
    def on_file_click(self, file_info: dict):
        """点击文件/文件夹"""
        if file_info['is_dir']:
            self.current_path = os.path.join(self.current_path, file_info['name'])
            self.refresh_files()
        else:
            self.show_snackbar(f"文件: {file_info['name']}", Config.INFO)
    
    def go_up(self):
        """返回上级目录"""
        if self.current_path != "/":
            self.current_path = os.path.dirname(self.current_path)
            self.refresh_files()
    
    # ================= 工具标签 =================
    def get_tool_tab(self):
        """工具箱"""
        tools = [
            ("截屏", ft.icons.SCREENSHOT, self.quick_screenshot, Config.PRIMARY),
            ("录屏", ft.icons.VIDEOCAM, self.start_recording_ui, Config.ERROR),
            ("亮度调节", ft.icons.BRIGHTNESS_6, self.brightness_dialog, Config.WARNING),
            ("屏幕超时", ft.icons.TIMER, self.timeout_dialog, Config.INFO),
            ("WiFi开关", ft.icons.WIFI, self.toggle_wifi, Config.SUCCESS),
            ("蓝牙开关", ft.icons.BLUETOOTH, self.toggle_bluetooth, Config.INFO),
            ("飞行模式", ft.icons.AIRPLANEMODE_ON, self.toggle_airplane, Config.WARNING),
            ("手电筒", ft.icons.FLASH_ON, self.toggle_flashlight, Config.ERROR),
            ("HOME键", ft.icons.HOME, lambda e: ADBTool.send_keyevent(3), Config.PRIMARY),
            ("返回键", ft.icons.ARROW_BACK, lambda e: ADBTool.send_keyevent(4), Config.WARNING),
            ("菜单键", ft.icons.MENU, lambda e: ADBTool.send_keyevent(82), Config.INFO),
            ("电源键", ft.icons.POWER_SETTINGS_NEW, lambda e: ADBTool.send_keyevent(26), Config.ERROR),
            ("音量+", ft.icons.VOLUME_UP, lambda e: ADBTool.send_keyevent(24), Config.PRIMARY),
            ("音量-", ft.icons.VOLUME_DOWN, lambda e: ADBTool.send_keyevent(25), Config.WARNING),
            ("清理后台", ft.icons.CLEAR_ALL, lambda e: ADBTool.run_shell_command("am kill-all"), Config.ERROR),
            ("打开设置", ft.icons.SETTINGS, lambda e: ADBTool.run_shell_command("am start -a android.settings.SETTINGS"), Config.INFO),
            ("打开相机", ft.icons.CAMERA, lambda e: ADBTool.run_shell_command("am start -a android.media.action.IMAGE_CAPTURE"), Config.SUCCESS),
            ("打开浏览器", ft.icons.LANGUAGE, self.open_browser_dialog, Config.PRIMARY),
            ("发送文本", ft.icons.TEXT_FIELDS, self.send_text_dialog, Config.INFO),
            ("模拟点击", ft.icons.TOUCH_APP, self.tap_dialog, Config.WARNING),
            ("模拟滑动", ft.icons.SWIPE, self.swipe_dialog, Config.ERROR),
        ]
        
        return ft.Column(
            [
                ft.Container(
                    content=ft.Text("工具箱", size=24, weight=ft.FontWeight.BOLD),
                    padding=20,
                ),
                
                ft.GridView(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Icon(icon, color=color, size=32),
                                        ft.Text(name, size=12, text_align=ft.TextAlign.CENTER),
                                    ],
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=10,
                                ),
                                padding=15,
                                on_click=func,
                            ),
                        )
                        for name, icon, func, color in tools
                    ],
                    runs_count=3,
                    max_extent=120,
                    child_aspect_ratio=1.0,
                    spacing=10,
                    run_spacing=10,
                    expand=True,
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.AUTO,
        )
    
    def start_recording_ui(self, e):
        """开始录屏"""
        ADBTool.start_recording()
        self.show_snackbar("录屏已开始，30秒后自动停止", Config.SUCCESS)
    
    def brightness_dialog(self, e):
        """亮度调节对话框"""
        slider = ft.Slider(min=0, max=255, value=ADBTool.get_brightness(), divisions=255)
        
        def on_apply(ev):
            ADBTool.set_brightness(int(slider.value))
            self.show_snackbar(f"亮度已设置为 {int(slider.value)}", Config.SUCCESS)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("屏幕亮度"),
            content=ft.Column([slider], tight=True),
            actions=[
                ft.TextButton("取消", on_click=lambda e: setattr(self.page.dialog, 'open', False)),
                ft.TextButton("应用", on_click=on_apply),
            ],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def timeout_dialog(self, e):
        """屏幕超时对话框"""
        options = [("30秒", 30), ("1分钟", 60), ("5分钟", 300), ("10分钟", 600), ("永不", 2147483647)]
        
        def on_select(ev):
            seconds = int(ev.control.key)
            ADBTool.set_screen_timeout(seconds)
            self.show_snackbar("已设置屏幕超时", Config.SUCCESS)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("屏幕超时"),
            content=ft.Column(
                [ft.ElevatedButton(text, key=str(sec), on_click=on_select) for text, sec in options],
                tight=True,
            ),
        )
        self.page.dialog.open = True
        self.page.update()
    
    def send_text_dialog(self, e):
        """发送文本对话框"""
        text_field = ft.TextField(hint_text="输入要发送的文本", multiline=True)
        
        def on_send(ev):
            if text_field.value:
                ADBTool.send_text(text_field.value)
                self.show_snackbar("已发送文本", Config.SUCCESS)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("发送文本"),
            content=ft.Column([text_field], tight=True),
            actions=[
                ft.TextButton("取消", on_click=lambda e: setattr(self.page.dialog, 'open', False)),
                ft.TextButton("发送", on_click=on_send),
            ],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def tap_dialog(self, e):
        """模拟点击对话框"""
        x_field = ft.TextField(label="X坐标", value="540")
        y_field = ft.TextField(label="Y坐标", value="960")
        
        def on_tap(ev):
            try:
                x, y = int(x_field.value), int(y_field.value)
                ADBTool.send_tap(x, y)
                self.show_snackbar(f"已点击 ({x}, {y})", Config.SUCCESS)
            except:
                self.show_snackbar("坐标格式错误", Config.ERROR)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("模拟点击"),
            content=ft.Column([x_field, y_field], tight=True),
            actions=[
                ft.TextButton("取消"),
                ft.TextButton("点击", on_click=on_tap),
            ],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def swipe_dialog(self, e):
        """模拟滑动对话框"""
        x1_field = ft.TextField(label="起点X", value="540")
        y1_field = ft.TextField(label="起点Y", value="1500")
        x2_field = ft.TextField(label="终点X", value="540")
        y2_field = ft.TextField(label="终点Y", value="500")
        
        def on_swipe(ev):
            try:
                x1, y1 = int(x1_field.value), int(y1_field.value)
                x2, y2 = int(x2_field.value), int(y2_field.value)
                ADBTool.send_swipe(x1, y1, x2, y2)
                self.show_snackbar("已执行滑动", Config.SUCCESS)
            except:
                self.show_snackbar("坐标格式错误", Config.ERROR)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("模拟滑动"),
            content=ft.Column([x1_field, y1_field, x2_field, y2_field], tight=True),
            actions=[
                ft.TextButton("取消"),
                ft.TextButton("滑动", on_click=on_swipe),
            ],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def open_browser_dialog(self, e):
        """打开浏览器对话框"""
        url_field = ft.TextField(label="网址", value="https://www.baidu.com", expand=True)
        
        def on_open(ev):
            if url_field.value:
                ADBTool.run_shell_command(f"am start -a android.intent.action.VIEW -d '{url_field.value}'")
                self.show_snackbar("已打开浏览器", Config.SUCCESS)
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("打开网页"),
            content=ft.Column([url_field], tight=True),
            actions=[
                ft.TextButton("取消"),
                ft.TextButton("打开", on_click=on_open),
            ],
        )
        self.page.dialog.open = True
        self.page.update()
    
    def toggle_bluetooth(self, e):
        """切换蓝牙"""
        ADBTool.bluetooth_enable()
        self.show_snackbar("已切换蓝牙状态", Config.INFO)
    
    # ================= 信息标签 =================
    def get_info_tab(self):
        """设备信息"""
        info = ADBTool.get_device_info()
        network = ADBTool.get_network_info()
        
        info_cards = []
        
        # 基本信息
        for key, value in info.items():
            info_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"{key}:", size=12, weight=ft.FontWeight.BOLD, width=100),
                                ft.Text(str(value), size=12, expand=True),
                            ],
                        ),
                        padding=10,
                    ),
                )
            )
        
        # 网络信息
        for key, value in network.items():
            info_cards.append(
                ft.Card(
                    content=ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(f"{key}:", size=12, weight=ft.FontWeight.BOLD, width=100),
                                ft.Text(str(value), size=12, expand=True),
                            ],
                        ),
                        padding=10,
                    ),
                )
            )
        
        # Root状态
        root_status = "已获取" if ADBTool.check_root() else "未获取"
        info_cards.append(
            ft.Card(
                content=ft.Container(
                    content=ft.Row(
                        [
                            ft.Text("ROOT权限:", size=12, weight=ft.FontWeight.BOLD, width=100),
                            ft.Text(root_status, size=12, color=Config.SUCCESS if root_status == "已获取" else Config.ERROR),
                        ],
                    ),
                    padding=10,
                ),
            )
        )
        
        return ft.Column(
            [
                ft.Container(
                    content=ft.Text("设备信息", size=24, weight=ft.FontWeight.BOLD),
                    padding=20,
                ),
                
                ft.ElevatedButton(
                    "刷新信息",
                    icon=ft.icons.REFRESH,
                    on_click=lambda e: self.on_nav_change(type('obj', (), {'control': type('obj', (), {'selected_index': 4})}())),
                ),
                
                ft.Divider(),
                
                ft.Column(info_cards, scroll=ft.ScrollMode.AUTO, expand=True),
            ],
            expand=True,
        )

# ================= 主函数 =================
def main(page: ft.Page):
    app = QClawADBApp(page)

if __name__ == "__main__":
    ft.app(target=main)
