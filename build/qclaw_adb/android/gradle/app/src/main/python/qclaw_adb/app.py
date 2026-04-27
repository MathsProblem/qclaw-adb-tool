"""
QClaw ADB Tool - 主应用
使用Toga框架的跨平台ADB管理工具
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW
import subprocess
import os
import sys


class ADBController:
    """ADB控制器"""

    def __init__(self):
        self.adb_path = self._find_adb()
        self.current_device = None

    def _find_adb(self):
        """查找ADB路径"""
        # Windows
        if sys.platform == 'win32':
            paths = [
                os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
                'adb.exe'
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
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

    def get_devices(self):
        """获取设备列表"""
        code, out, err = self._run_adb(['devices', '-l'])
        if code != 0:
            return []

        devices = []
        lines = out.strip().split('\n')
        for line in lines[1:]:
            if line.strip():
                parts = line.split()
                if len(parts) >= 2 and parts[1] == 'device':
                    devices.append(parts[0])
        return devices

    def shell(self, device_id, command):
        """执行Shell命令"""
        if device_id:
            code, out, err = self._run_adb(['-s', device_id, 'shell', command], timeout=60)
        else:
            code, out, err = self._run_adb(['shell', command], timeout=60)
        return out if code == 0 else err

    def get_device_info(self, device_id=None):
        """获取设备信息"""
        info = {}
        props = [
            ('brand', 'ro.product.brand'),
            ('model', 'ro.product.model'),
            ('android', 'ro.build.version.release'),
            ('sdk', 'ro.build.version.sdk'),
        ]
        for name, prop in props:
            out = self.shell(device_id, f'getprop {prop}')
            info[name] = out.strip()
        return info

    def list_packages(self, device_id=None):
        """列出应用"""
        out = self.shell(device_id, 'pm list packages -3')
        packages = []
        for line in out.strip().split('\n'):
            if line.startswith('package:'):
                packages.append(line.replace('package:', '').strip())
        return packages

    def screenshot(self, device_id=None):
        """截屏"""
        remote_path = '/sdcard/qclaw_screenshot.png'
        self.shell(device_id, f'screencap -p {remote_path}')

        local_path = os.path.join(os.getcwd(), 'qclaw_screenshot.png')
        if device_id:
            self._run_adb(['-s', device_id, 'pull', remote_path, local_path])
        else:
            self._run_adb(['pull', remote_path, local_path])

        return os.path.exists(local_path), local_path

    def uninstall(self, device_id, package):
        """卸载应用"""
        code, out, err = self._run_adb(['-s', device_id, 'uninstall', package])
        return code == 0, out or err


class QClawADBApp(toga.App):
    """主应用类"""

    def startup(self):
        """启动应用"""
        self.adb = ADBController()

        # 主容器
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10, gap=10))

        # 标题
        title_label = toga.Label(
            "QClaw ADB Tool",
            style=Pack(padding=10, font_size=24, font_weight='bold')
        )
        main_box.add(title_label)

        # 设备选择
        device_box = toga.Box(style=Pack(direction=ROW, padding=5, gap=10))

        self.device_selector = toga.Selection(
            style=Pack(flex=1, padding=5),
            on_select=self.on_device_select
        )

        refresh_btn = toga.Button(
            "🔄",
            style=Pack(padding=5, width=50),
            on_press=self.refresh_devices
        )

        device_box.add(self.device_selector)
        device_box.add(refresh_btn)
        main_box.add(device_box)

        # 状态标签
        self.status_label = toga.Label(
            "就绪",
            style=Pack(padding=5, font_size=12)
        )
        main_box.add(self.status_label)

        # 功能按钮
        button_box = toga.Box(style=Pack(direction=COLUMN, padding=10, gap=10))

        buttons = [
            ("📱 设备信息", self.show_device_info),
            ("📦 应用列表", self.show_packages),
            ("📸 截屏", self.take_screenshot),
            ("💻 Shell", self.open_shell),
            ("📶 无线连接", self.connect_wifi),
            ("❓ 关于", self.show_about),
        ]

        for text, handler in buttons:
            btn = toga.Button(
                text,
                style=Pack(padding=10, font_size=16),
                on_press=handler
            )
            button_box.add(btn)

        main_box.add(button_box)

        # 输出区域
        self.output_label = toga.Label(
            "欢迎使用 QClaw ADB Tool",
            style=Pack(padding=10, flex=1)
        )

        scroll_box = toga.ScrollContainer(style=Pack(flex=1, padding=5))
        scroll_box.content = self.output_label
        main_box.add(scroll_box)

        # 创建主窗口
        self.main_window = toga.MainWindow(title="QClaw ADB Tool", size=(400, 700))
        self.main_window.content = main_box
        self.main_window.show()

        # 自动刷新设备
        self.refresh_devices(None)

    def refresh_devices(self, widget):
        """刷新设备列表"""
        devices = self.adb.get_devices()

        self.device_selector.items = devices if devices else ['未检测到设备']

        if devices:
            self.device_selector.value = devices[0]
            self.adb.current_device = devices[0]
            self.status_label.text = f"已连接 {len(devices)} 台设备"
        else:
            self.device_selector.value = '未检测到设备'
            self.adb.current_device = None
            self.status_label.text = "未检测到设备"

    def on_device_select(self, widget):
        """选择设备"""
        value = widget.value
        if value and value != '未检测到设备':
            self.adb.current_device = value
            self.status_label.text = f"已选择: {value}"

    def show_device_info(self, widget):
        """显示设备信息"""
        if not self.adb.current_device:
            self.status_label.text = "请先选择设备"
            return

        info = self.adb.get_device_info(self.adb.current_device)
        text = f"""设备信息
━━━━━━━━━━━━━━━━━━
品牌: {info.get('brand', 'N/A')}
型号: {info.get('model', 'N/A')}
Android: {info.get('android', 'N/A')}
SDK: {info.get('sdk', 'N/A')}
设备: {self.adb.current_device}
"""
        self.output_label.text = text

    def show_packages(self, widget):
        """显示应用列表"""
        if not self.adb.current_device:
            self.status_label.text = "请先选择设备"
            return

        self.status_label.text = "正在获取应用列表..."
        packages = self.adb.list_packages(self.adb.current_device)

        text = f"已安装应用 ({len(packages)}个):\n"
        text += "\n".join(f"• {pkg}" for pkg in packages[:20])
        if len(packages) > 20:
            text += f"\n... 还有 {len(packages)-20} 个应用"

        self.output_label.text = text
        self.status_label.text = "获取完成"

    def take_screenshot(self, widget):
        """截屏"""
        if not self.adb.current_device:
            self.status_label.text = "请先选择设备"
            return

        self.status_label.text = "正在截屏..."
        success, path = self.adb.screenshot(self.adb.current_device)

        if success:
            self.output_label.text = f"截屏成功！\n保存至: {path}"
            self.status_label.text = "截屏完成"
        else:
            self.output_label.text = "截屏失败"
            self.status_label.text = "就绪"

    def open_shell(self, widget):
        """打开Shell"""
        if not self.adb.current_device:
            self.status_label.text = "请先选择设备"
            return

        self.output_label.text = """Shell命令提示

常用命令:
• pm list packages - 列出应用
• pm uninstall <包名> - 卸载应用
• am start -n <包名>/<Activity> - 启动应用
• input text <文本> - 输入文本
• input tap <x> <y> - 点击坐标
• screencap -p /sdcard/scr.png - 截屏

请在终端中执行: adb shell
"""
        self.status_label.text = "查看Shell提示"

    def connect_wifi(self, widget):
        """无线连接"""
        self.output_label.text = """无线连接步骤

1. 确保设备和电脑在同一WiFi网络
2. 在设备上启用无线调试
3. 获取设备IP地址
4. 执行配对: adb pair <IP>:<端口>
5. 连接设备: adb connect <IP>:5555

示例:
  adb pair 192.168.1.100:37123
  adb connect 192.168.1.100:5555
"""
        self.status_label.text = "查看无线连接说明"

    def show_about(self, widget):
        """显示关于"""
        self.output_label.text = """QClaw ADB Tool v1.0.0

一个强大的Android设备管理工具

功能:
• 设备信息查询
• 应用管理
• 截屏功能
• Shell命令执行
• 无线连接支持

作者: QClaw
开源: github.com/MathsProblem/qclaw-adb-tool
"""
        self.status_label.text = "关于"


def main():
    """主入口"""
    return QClawADBApp("QClaw ADB Tool", "org.qclaw.qclaw_adb")


if __name__ == '__main__':
    main().main_loop()
