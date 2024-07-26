#############################################################################################################################
#  Mouse.Clickz                                                                                                             #
#  Created by alby13                                                                                                        #
#############################################################################################################################

import sys
import json
from datetime import datetime, timedelta
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QSystemTrayIcon, QMenu, QAction, QStyle
from PyQt5.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt5.QtGui import QIcon
from pynput import mouse

class MouseHandler(QObject):
    left_clicked = pyqtSignal()
    right_clicked = pyqtSignal()
    middle_clicked = pyqtSignal()
    scrolled_up = pyqtSignal()
    scrolled_down = pyqtSignal()
    moved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.listener = mouse.Listener(
            on_click=self.on_click,
            on_scroll=self.on_scroll,
            on_move=self.on_move
        )
        self.listener.start()

    def on_click(self, x, y, button, pressed):
        if pressed:
            if button == mouse.Button.left:
                self.left_clicked.emit()
            elif button == mouse.Button.right:
                self.right_clicked.emit()
            elif button == mouse.Button.middle:
                self.middle_clicked.emit()

    def on_scroll(self, x, y, dx, dy):
        if dy > 0:
            self.scrolled_up.emit()
        elif dy < 0:
            self.scrolled_down.emit()

    def on_move(self, x, y):
        self.moved.emit()

class ClickCounter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.left_clicks = 0
        self.right_clicks = 0
        self.scroll_ups = 0
        self.scroll_downs = 0
        self.scroll_clicks = 0
        self.distinct_moves = 0
        self.start_time = datetime.now()
        self.total_runtime = timedelta()
        self.last_saved = {'left': 0, 'right': 0, 'scroll_ups': 0, 'scroll_downs': 0, 'scroll_clicks': 0, 'mouse_moves': 0, 'total_runtime': 0}
        self.load_clicks()
        self.initUI()
        
        self.mouse_handler = MouseHandler()
        self.mouse_handler.left_clicked.connect(self.on_left_click)
        self.mouse_handler.right_clicked.connect(self.on_right_click)
        self.mouse_handler.middle_clicked.connect(self.on_middle_click)
        self.mouse_handler.scrolled_up.connect(self.on_scroll_up)
        self.mouse_handler.scrolled_down.connect(self.on_scroll_down)
        self.mouse_handler.moved.connect(self.on_mouse_move)

        self.timer = QTimer()
        self.timer.timeout.connect(self.save_clicks)
        self.timer.start(3600000)  # Save every hour (3600000 ms)

        self.move_timer = QTimer()
        self.move_timer.setSingleShot(True)
        self.move_timer.timeout.connect(self.mouse_stopped)
        self.is_mouse_moving = False

        # Update runtime every second
        self.runtime_timer = QTimer()
        self.runtime_timer.timeout.connect(self.update_runtime)
        self.runtime_timer.start(1000)


    def initUI(self):
        self.setWindowTitle('Mouse Clicks by alby13')
        self.setGeometry(300, 300, 250, 200)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()

        self.left_label = QLabel(f'Left Clicks: {self.left_clicks}')
        self.right_label = QLabel(f'Right Clicks: {self.right_clicks}')
        self.scroll_up_label = QLabel(f'Scroll Ups: {self.scroll_ups}')
        self.scroll_down_label = QLabel(f'Scroll Downs: {self.scroll_downs}')
        self.scroll_click_label = QLabel(f'Scroll Clicks: {self.scroll_clicks}')
        self.move_label = QLabel(f'Mouse Moves: {self.distinct_moves}')
        self.runtime_label = QLabel(f'Total Runtime: {str(self.total_runtime).split(".")[0]}')

        layout.addWidget(self.left_label)
        layout.addWidget(self.right_label)
        layout.addWidget(self.scroll_up_label)
        layout.addWidget(self.scroll_down_label)
        layout.addWidget(self.scroll_click_label)
        layout.addWidget(self.move_label)
        layout.addWidget(self.runtime_label)

        central_widget.setLayout(layout)

        # Update runtime every second
        self.runtime_timer = QTimer()
        self.runtime_timer.timeout.connect(self.update_runtime)
        self.runtime_timer.start(1000)

    def on_left_click(self):
        self.left_clicks += 1
        self.left_label.setText(f'Left Clicks: {self.left_clicks}')

    def on_right_click(self):
        self.right_clicks += 1
        self.right_label.setText(f'Right Clicks: {self.right_clicks}')

    def on_middle_click(self):
        self.scroll_clicks += 1
        self.scroll_click_label.setText(f'Scroll Clicks: {self.scroll_clicks}')

    def on_scroll_up(self):
        self.scroll_ups += 1
        self.scroll_up_label.setText(f'Scroll Ups: {self.scroll_ups}')

    def on_scroll_down(self):
        self.scroll_downs += 1
        self.scroll_down_label.setText(f'Scroll Downs: {self.scroll_downs}')

    def on_mouse_move(self):
        if not self.is_mouse_moving:
            self.is_mouse_moving = True
            self.distinct_moves += 1
            self.move_label.setText(f'Mouse Moves: {self.distinct_moves}')
        self.move_timer.start(5000)  # 5 seconds of no movement for mouse stopped
        
    def mouse_stopped(self):
        self.is_mouse_moving = False

    def load_clicks(self):
        try:
            with open('click_counts.json', 'r') as f:
                data = json.load(f)
                self.left_clicks = data['left']
                self.right_clicks = data['right']
                self.scroll_ups = data['scroll_ups']
                self.scroll_downs = data['scroll_downs']
                self.scroll_clicks = data['scroll_clicks']
                self.distinct_moves = data['distinct_moves']
                self.total_runtime = timedelta(seconds=data['total_runtime'])
                self.last_saved = data.copy()
        except FileNotFoundError:
            print("No previous data found. Starting fresh.")
        except Exception as e:
            print(f"Error loading clicks: {e}")

    def save_clicks(self):
        current_runtime = self.total_runtime + (datetime.now() - self.start_time)
        current = {
            'left': self.left_clicks,
            'right': self.right_clicks,
            'scroll_ups': self.scroll_ups,
            'scroll_downs': self.scroll_downs,
            'scroll_clicks': self.scroll_clicks,
            'distinct_moves': self.distinct_moves,
            'total_runtime': int(current_runtime.total_seconds())
        }
        if current != self.last_saved:
            with open('click_counts.json', 'w') as f:
                json.dump(current, f)
                self.last_saved = current.copy()

    def update_runtime(self):
        current_runtime = self.total_runtime + (datetime.now() - self.start_time)
        self.runtime_label.setText(f'Total Runtime: {str(current_runtime).split(".")[0]}')

    def quit_app(self):
        self.save_clicks()
        QApplication.instance().quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = ClickCounter()
    ex.show()
    sys.exit(app.exec_())
