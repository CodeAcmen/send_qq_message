import sys
import webbrowser
import subprocess
import pyautogui
import time
import platform
import threading
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QListWidget, QMessageBox, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QIcon

class Command:
    def __init__(self, message, interval, max_executions):
        self.message = message
        self.interval = interval
        self.max_executions = max_executions
        self.executions = 0
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
        message = self.message_input.text()
        interval = self.time_input.text()
        max_executions = self.count_input.text()
        
        if not interval.isdigit() or int(interval) <= 0:
            QMessageBox.warning(self, '错误', '请输入有效的时间间隔（大于0的数字）。')
            return
        
        if not max_executions.isdigit() or int(max_executions) <= 0 or int(max_executions) > 50:
            QMessageBox.warning(self, '错误', '请输入有效的执行次数（1到50之间的数字）。')
            return
        
        command = Command(message, int(interval) * 1000, int(max_executions))
        command.timer.timeout.connect(lambda: self.run_in_thread(command))
        self.commands.append(command)
        self.command_list.addItem(f'消息: {message}, 间隔: {interval}秒, 次数: {max_executions}')
        
    def open_and_minimize_group_chat(self):
        # 打开群聊窗口
        webbrowser.open(f'tencent://groupwpa/?subcmd=all&param={self.group_param}')
        time.sleep(5)  # 等待群聊窗口打开

        # 最小化窗口
        if platform.system() == "Windows":
            pyautogui.hotkey('win', 'down')  # 确保窗口最小化
        elif platform.system() == "Darwin":
            pyautogui.hotkey('command', 'm')  # macOS最小化窗口

        QMessageBox.information(self, '信息', '请确保群聊窗口已最小化。')

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
            # 将QQ窗口前置以确保发送消息
            if platform.system() == "Windows":
                pyautogui.hotkey('alt', 'tab')
            elif platform.system() == "Darwin":
                pyautogui.hotkey('command', 'tab')

            pyautogui.typewrite(command.message)
            pyautogui.press('enter')
            
            command.executions += 1
            
            if command.executions >= command.max_executions:
                command.timer.stop()
                QMessageBox.information(self, '完成', f'命令已完成：消息: {command.message}')
        except Exception as e:
            QMessageBox.warning(self, '错误', f'执行过程中出现错误：{str(e)}')
            command.timer.stop()

    def show_notification(self, title, message):
        if platform.system() == "Windows":
            script = f'''
            powershell -Command "New-BurntToastNotification -Text '{title}', '{message}'"
            '''
            subprocess.run(["powershell", "-Command", script], shell=True)
        elif platform.system() == "Darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])

def main():
    app = QApplication(sys.argv)
    ex = ClipboardChecker()
    ex.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
