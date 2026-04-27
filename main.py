#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QClaw ADB Tool - Android版ADB管理工具
使用Kivy框架，适配Android系统
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle

import subprocess
import os
import sys

# 平台检测
try:
    from kivy.utils import platform
    IS_ANDROID = platform == 'android'
except:
    IS_ANDROID = False

if IS_ANDROID:
    from android import mActivity
    from jnius import autoclass
    Environment = autoclass('android.os.Environment')
    PythonActivity = autoclass('org.kivy.android.PythonActivity')


class ADBController:
    """ADB控制器"""
    
    def __init__(self):
        self.adb_path = self._find_adb()
        
    def _find_adb(self):
        """查找ADB路径"""
        if IS_ANDROID:
            # Android环境，使用内置adb或termux adb
            paths = [
                '/data/data/com.termux/files/usr/bin/adb',
                '/system/bin/adb',
            ]
            for path in paths:
                if os.path.exists(path):
                    return path
        return 'adb'
    
    def _run_cmd(self, args, timeout=30):
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
        code, out, err = self._run_cmd(['devices', '-l'])
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
            code, out, err = self._run_cmd(['-s', device_id, 'shell', command], timeout=60)
        else:
            code, out, err = self._run_cmd(['shell', command], timeout=60)
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
        
        if IS_ANDROID:
            local_path = os.path.join(
                Environment.getExternalStorageDirectory().getAbsolutePath(),
                'qclaw_screenshot.png'
            )
        else:
            local_path = 'qclaw_screenshot.png'
        
        if device_id:
            self._run_cmd(['-s', device_id, 'pull', remote_path, local_path])
        else:
            self._run_cmd(['pull', remote_path, local_path])
        
        return os.path.exists(local_path), local_path


class MainScreen(Screen):
    """主界面"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.adb = ADBController()
        self.current_device = None
        self.build_ui()
    
    def build_ui(self):
        """构建UI"""
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        
        # 标题
        title = Label(
            text='[size=24][b]QClaw ADB Tool[/b][/size]',
            markup=True,
            size_hint_y=None,
            height=dp(50)
        )
        layout.add_widget(title)
        
        # 设备选择
        device_box = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(10))
        self.device_spinner = Spinner(
            text='选择设备',
            values=['刷新中...'],
            size_hint_x=0.7
        )
        self.device_spinner.bind(text=self.on_device_select)
        
        refresh_btn = Button(
            text='🔄',
            size_hint_x=0.15,
            font_size=dp(20)
        )
        refresh_btn.bind(on_press=self.refresh_devices)
        
        device_box.add_widget(self.device_spinner)
        device_box.add_widget(refresh_btn)
        layout.add_widget(device_box)
        
        # 状态栏
        self.status_label = Label(
            text='就绪',
            size_hint_y=None,
            height=dp(30),
            font_size=dp(14),
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(self.status_label)
        
        # 功能按钮
        btn_layout = BoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(5)
        )
        
        buttons = [
            ('📱 设备信息', self.show_device_info),
            ('📦 应用列表', self.show_packages),
            ('📸 截屏', self.take_screenshot),
            ('💻 Shell命令', self.open_shell),
            ('📶 无线连接', self.connect_wifi),
        ]
        
        for text, handler in buttons:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(60),
                font_size=dp(18)
            )
            btn.bind(on_press=handler)
            btn_layout.add_widget(btn)
        
        layout.add_widget(btn_layout)
        
        # 输出区域
        self.output_label = Label(
            text='欢迎使用 QClaw ADB Tool',
            size_hint_y=None,
            height=dp(100),
            valign='top',
            text_size=(Window.width - dp(20), None),
            halign='left'
        )
        
        scroll = ScrollView()
        scroll.add_widget(self.output_label)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
        
        # 自动刷新设备
        Clock.schedule_once(lambda dt: self.refresh_devices(None), 1)
    
    def refresh_devices(self, instance):
        """刷新设备列表"""
        devices = self.adb.get_devices()
        if devices:
            self.device_spinner.values = devices
            self.device_spinner.text = devices[0]
            self.current_device = devices[0]
            self.status_label.text = f'已连接 {len(devices)} 台设备'
        else:
            self.device_spinner.values = ['未检测到设备']
            self.device_spinner.text = '未检测到设备'
            self.current_device = None
            self.status_label.text = '未检测到设备'
    
    def on_device_select(self, spinner, text):
        """选择设备"""
        if text and text != '未检测到设备' and text != '刷新中...':
            self.current_device = text
    
    def show_device_info(self, instance):
        """显示设备信息"""
        if not self.current_device:
            self.show_popup('提示', '请先选择设备')
            return
        
        info = self.adb.get_device_info(self.current_device)
        text = f"""设备信息
━━━━━━━━━━━━━━━━
品牌: {info.get('brand', 'N/A')}
型号: {info.get('model', 'N/A')}
Android: {info.get('android', 'N/A')}
SDK: {info.get('sdk', 'N/A')}
设备: {self.current_device}
"""
        self.output_label.text = text
    
    def show_packages(self, instance):
        """显示应用列表"""
        if not self.current_device:
            self.show_popup('提示', '请先选择设备')
            return
        
        self.status_label.text = '正在获取应用列表...'
        packages = self.adb.list_packages(self.current_device)
        
        text = f"已安装应用 ({len(packages)}个):\n"
        text += "\n".join(f"• {pkg}" for pkg in packages[:20])
        if len(packages) > 20:
            text += f"\n... 还有 {len(packages)-20} 个应用"
        
        self.output_label.text = text
        self.status_label.text = '获取完成'
    
    def take_screenshot(self, instance):
        """截屏"""
        if not self.current_device:
            self.show_popup('提示', '请先选择设备')
            return
        
        self.status_label.text = '正在截屏...'
        success, path = self.adb.screenshot(self.current_device)
        
        if success:
            self.output_label.text = f'截屏成功！\n保存至: {path}'
            self.show_popup('成功', f'截图已保存至\n{path}')
        else:
            self.output_label.text = '截屏失败'
        
        self.status_label.text = '就绪'
    
    def open_shell(self, instance):
        """打开Shell"""
        if not self.current_device:
            self.show_popup('提示', '请先选择设备')
            return
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        input_field = TextInput(
            hint_text='输入Shell命令',
            multiline=False,
            size_hint_y=None,
            height=dp(50)
        )
        
        output = Label(
            text='输出将显示在这里',
            valign='top',
            halign='left',
            text_size=(None, None)
        )
        
        content.add_widget(input_field)
        content.add_widget(output)
        
        def execute_cmd(instance):
            cmd = input_field.text.strip()
            if cmd:
                result = self.adb.shell(self.current_device, cmd)
                output.text = result
        
        input_field.bind(on_text_validate=execute_cmd)
        
        popup = Popup(
            title='Shell命令',
            content=content,
            size_hint=(0.9, 0.7)
        )
        popup.open()
    
    def connect_wifi(self, instance):
        """无线连接"""
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(10))
        
        input_field = TextInput(
            hint_text='IP:端口 (如 192.168.1.100:5555)',
            multiline=False,
            size_hint_y=None,
            height=dp(50)
        )
        
        status = Label(text='')
        
        def do_connect(instance):
            ip_port = input_field.text.strip()
            if ip_port:
                status.text = f'正在连接 {ip_port}...'
                code, out, err = self.adb._run_cmd(['connect', ip_port])
                if code == 0:
                    status.text = f'连接结果:\n{out}'
                    self.refresh_devices(None)
                else:
                    status.text = f'连接失败:\n{err}'
        
        connect_btn = Button(text='连接', size_hint_y=None, height=dp(50))
        connect_btn.bind(on_press=do_connect)
        
        content.add_widget(input_field)
        content.add_widget(connect_btn)
        content.add_widget(status)
        
        popup = Popup(
            title='无线连接',
            content=content,
            size_hint=(0.9, 0.5)
        )
        popup.open()
    
    def show_popup(self, title, message):
        """显示弹窗"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.7, 0.3)
        )
        popup.open()


class QClawADBApp(App):
    """应用主类"""
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        return sm


if __name__ == '__main__':
    from kivy.clock import Clock
    QClawADBApp().run()
