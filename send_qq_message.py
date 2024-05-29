import sys
import webbrowser
import ctypes
import time
import threading
import pygetwindow as gw
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

class Command:
    def __init__(self, message, interval, max_executions, window_title):
        self.message = message
        self.interval = interval
        self.max_executions = max_executions
        self.executions = 0
        self.window_title = window_title
        self.timer = QTimer()

class ClipboardChecker(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.max_executions = 50
        self.group_param = "7b2267726f757055696e223a3239363232393136372c2274696d655374616d70223a313731363836373233392c22617574684b6579223a22766f54465a52786b74524e2f666441396b35765263765a70636a2b564c7636664b72677a50684654516941675a4e39375253326d4a786e656c436a67347a722f222c2261757468223a22227d"
        self.commands = []
        self.init_tray()

    def initUI(self):
        self.setWindowTitle('Clipboard Checker')
        self.setGeometry(100, 100, 500, 400)
        
        layout = QVBoxLayout()
        
        self.command_list = QListWidget(self)
        layout.addWidget(self.command_list)
        
        form_layout = QVBoxLayout()
        
        self.window_title_label = QLabel('请输入群聊窗口标题:', self)
        form_layout.addWidget(self.window_title_label)
        
        self.window_title_input = QLineEdit(self)
        form_layout.addWidget(self.window_title_input)
        
        self.message_label = QLabel('请输入消息内容:', self)
        form_layout.addWidget(self.message_label)
        
        self.message_input = QLineEdit(self)
        form_layout.addWidget(self.message_input)
        
        self.time_label = QLabel('请输入时间间隔（秒）:', self)
        form_layout.addWidget(self.time_label)
        
        self.time_input = QLineEdit(self)
        form_layout.addWidget(self.time_input)
        
        self.count_label = QLabel('请输入执行次数（最大不超过50次）:', self)
        form_layout.addWidget(self.count_label)
        
        self.count_input = QLineEdit(self)
        form_layout.addWidget(self.count_input)
        
        self.add_button = QPushButton('添加命令', self)
        self.add_button.clicked.connect(self.add_command)
        form_layout.addWidget(self.add_button)
        
        layout.addLayout(form_layout)
        
        self.start_button = QPushButton('打开并最小化群聊窗口', self)
        self.start_button.clicked.connect(self.open_and_minimize_group_chat)
        layout.addWidget(self.start_button)
        
        self.start_commands_button = QPushButton('开始所有命令', self)
        self.start_commands_button.clicked.connect(self.start_all_commands)
        layout.addWidget(self.start_commands_button)
        
        self.stop_button = QPushButton('停止所有命令', self)
        self.stop_button.clicked.connect(self.stop_all_commands)
        layout.addWidget(self.stop_button)
        
        self.setLayout(layout)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon('icon.png'))
        
        show_action = QAction("Show", self)
        quit_action = QAction("Exit", self)
        hide_action = QAction("Hide", self)
        
        show_action.triggered.connect(self.show)
        hide_action.triggered.connect(self.hide)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu = QMenu()
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def add_command(self):
        window_title = self.window_title_input.text()
        message = self.message_input.text()
        interval = self.time_input.text()
        max_executions = self.count_input.text()
        
        if not window_title:
            QMessageBox.warning(self, '错误', '群聊窗口标题不能为空。')
            return
        
        if not interval.isdigit() or int(interval) <= 0:
            QMessageBox.warning(self, '错误', '请输入有效的时间间隔（大于0的数字）。')
            return
        
        if not max_executions.isdigit() or int(max_executions) <= 0 or int(max_executions) > 50:
            QMessageBox.warning(self, '错误', '请输入有效的执行次数（1到50之间的数字）。')
            return
        
        command = Command(message, int(interval) * 1000, int(max_executions), window_title)
        command.timer.timeout.connect(lambda: self.run_in_thread(command))
        self.commands.append(command)
        self.command_list.addItem(f'标题: {window_title}, 消息: {message}, 间隔: {interval}秒, 次数: {max_executions}')
        
    def open_and_minimize_group_chat(self):
        window_title = self.window_title_input.text()
        if not window_title:
            QMessageBox.warning(self, '错误', '群聊窗口标题不能为空。')
            return
        
        # 打开群聊窗口
        webbrowser.open(f'tencent://groupwpa/?subcmd=all&param={self.group_param}')
        time.sleep(5)  # 等待群聊窗口打开

        # 查找并最小化特定群聊窗口
        windows = gw.getWindowsWithTitle(window_title)
        if windows:
            group_window = windows[0]
            group_window.minimize()
            QMessageBox.information(self, '信息', '群聊窗口已最小化。')
        else:
            QMessageBox.warning(self, '错误', f'未找到群聊窗口：{window_title}')

    def start_all_commands(self):
        for command in self.commands:
            command.timer.start(command.interval)
            self.show_notification(f'命令开始：消息: {command.message}', f'间隔: {command.interval//1000}秒, 次数: {command.max_executions}')
            
    def stop_all_commands(self):
        for command in self.commands:
            command.timer.stop()
        QMessageBox.information(self, '停止', '所有命令已停止。')

    def run_in_thread(self, command):
        thread = threading.Thread(target=self.send_message_to_group, args=(command,))
        thread.start()
        
    def send_message_to_group(self, command):
        try:
            # 获取 QQ 窗口
            windows = gw.getWindowsWithTitle(command.window_title)
            if not windows:
                print("群窗口未找到")
                return

            qq_window = windows[0]

            # 获取窗口句柄
            hwnd = qq_window._hWnd

            # 定义一些常量
            WM_SETTEXT = 0x000C
            WM_KEYDOWN = 0x0100
            WM_KEYUP = 0x0101
            VK_RETURN = 0x0D

            # 获取窗口的编辑框句柄 (需要根据实际情况调整)
            edit_hwnd = ctypes.windll.user32.FindWindowExW(hwnd, 0, "Edit", None)

            # 发送文本消息到编辑框
            if edit_hwnd:
                ctypes.windll.user32.SendMessageW(edit_hwnd, WM_SETTEXT, 0, command.message)
                # 发送回车键
                ctypes.windll.user32.SendMessageW(edit_hwnd, WM_KEYDOWN, VK_RETURN, 0)
                ctypes.windll.user32.SendMessageW(edit_hwnd, WM_KEYUP, VK_RETURN, 0)
            else:
                print("编辑框未找到")

            command.executions += 1
            print(f"Message sent. Executions: {command.executions}/{command.max_executions}")

            if command.executions >= command.max_executions:
                command.timer.stop()
                QMessageBox.information(self, '完成', f'命令已完成：消息: {command.message}')
        except Exception as e:
            print(f"Error: {str(e)}")
            QMessageBox.warning(self, '错误', f'执行过程中出现错误：{str(e)}')
            command.timer.stop()

    def show_notification(self, title, message):
        script = f'''
        powershell -Command "New-BurntToastNotification -Text '{title}', '{message}'"
        '''
        subprocess.run(["powershell", "-Command", script], shell=True)

def main():
    app = QApplication(sys.argv)
    ex = ClipboardChecker()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
