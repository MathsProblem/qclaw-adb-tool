"""
QClaw ADB Tool - 简化版
专为Android优化的ADB管理工具
"""

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW


class QClawADBApp(toga.App):
    """主应用类"""

    def startup(self):
        """启动应用"""
        # 主容器
        main_box = toga.Box(style=Pack(direction=COLUMN, padding=10))

        # 标题
        title = toga.Label(
            "QClaw ADB Tool v1.0",
            style=Pack(padding=20, font_size=20, font_weight='bold', text_align='center')
        )
        main_box.add(title)

        # 说明文字
        info = toga.Label(
            "Android ADB 管理工具\n\n" +
            "功能:\n" +
            "• 设备信息查询\n" +
            "• 应用管理\n" +
            "• 截屏功能\n" +
            "• Shell命令\n\n" +
            "注意: 需要USB调试权限",
            style=Pack(padding=10, text_align='center')
        )
        main_box.add(info)

        # 测试按钮
        test_btn = toga.Button(
            "测试应用",
            style=Pack(padding=20),
            on_press=self.test_click
        )
        main_box.add(test_btn)

        # 状态
        self.status = toga.Label(
            "就绪",
            style=Pack(padding=10, text_align='center')
        )
        main_box.add(self.status)

        # 创建主窗口
        self.main_window = toga.MainWindow(title="QClaw ADB Tool")
        self.main_window.content = main_box
        self.main_window.show()

    def test_click(self, widget):
        """测试点击"""
        self.status.text = "✓ 应用运行正常！"
        self.main_window.info_dialog("成功", "QClaw ADB Tool 运行正常！\n\n版本: 1.0.0\n平台: Android")


def main():
    """主入口"""
    return QClawADBApp("QClaw ADB Tool", "org.qclaw.qclaw_adb")


if __name__ == '__main__':
    main().main_loop()
