from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                             QFrame, QLabel, QComboBox, QTextEdit, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, Signal, Slot, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QTextCharFormat, QColor, QTextCursor

class LogPage(QWidget):
    """日志显示页面"""
    filter_changed = Signal(int) # 发送新的过滤等级

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filter_level = 0
        self.log_level_map = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
        self.setup_ui()
        
        # 初始透明度设置
        self.eff = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.eff)
        self.fade_anim = QPropertyAnimation(self.eff, b"opacity")
        self.fade_anim.setDuration(400)
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        self.fade_anim.start()

    def setup_ui(self):
        log_layout = QVBoxLayout(self)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(0)

        # 创建日志控制工具栏
        self.log_toolbar = QFrame()
        self.log_toolbar.setFixedHeight(40)
        self.log_toolbar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3c3c3c;")
        toolbar_layout = QHBoxLayout(self.log_toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)
        toolbar_layout.setSpacing(10)

        label_filter = QLabel("日志筛选:")
        label_filter.setStyleSheet("color: white;")
        toolbar_layout.addWidget(label_filter)
        self.level_filter = QComboBox()
        self.level_filter.addItems(["DEBUG", "INFO", "WARN", "ERROR"])
        self.level_filter.setStyleSheet("background-color: #3e3e42; color: white; border: 1px solid #454545; padding: 2px;")
        toolbar_layout.addWidget(self.level_filter)

        toolbar_layout.addStretch()

        self.btn_clear_logs = QPushButton("清除日志")
        self.btn_clear_logs.setCursor(Qt.PointingHandCursor)
        self.btn_clear_logs.setStyleSheet("""
            QPushButton { 
                background-color: #3e3e42; color: #cccccc; border: 1px solid #454545; 
                padding: 3px 12px; border-radius: 2px; font-size: 11px;
            }
            QPushButton:hover { background-color: #d13438; color: white; border: 1px solid #d13438; }
        """)
        toolbar_layout.addWidget(self.btn_clear_logs)
        log_layout.addWidget(self.log_toolbar)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: #d4d4d4; font-family: 'Consolas'; font-size: 12px; border: none;")
        log_layout.addWidget(self.log_view)

        # 信号绑定
        self.level_filter.currentIndexChanged.connect(self.on_filter_changed)

    def on_filter_changed(self, index):
        level_str = self.level_filter.currentText()
        self.current_filter_level = self.log_level_map.get(level_str, 0)
        self.filter_changed.emit(self.current_filter_level)

    def clear(self):
        self.log_view.clear()

    def append_log(self, log_obj):
        if self.log_level_map.get(log_obj['level'], 0) < self.current_filter_level:
            return

        # 确保日志始终插入在文本末尾
        self.log_view.moveCursor(QTextCursor.End)
        
        color_map = {
            "DEBUG": "#808080", "INFO": "#d4d4d4", "WARN": "#dcdcaa", "ERROR": "#f44747"
        }
        
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#565656"))
        self.log_view.setCurrentCharFormat(fmt)
        self.log_view.insertPlainText(f"[{log_obj['time']}] ")
        
        fmt.setForeground(QColor(color_map.get(log_obj['level'], "#d4d4d4")))
        fmt.setFontWeight(700)
        self.log_view.setCurrentCharFormat(fmt)
        self.log_view.insertPlainText(f"[{log_obj['level']}] ")
        
        fmt.setForeground(QColor("#d4d4d4"))
        fmt.setFontWeight(400)
        self.log_view.setCurrentCharFormat(fmt)
        
        content = log_obj['content']
        if not content.endswith('\n'):
            content += '\n'
            
        scrollbar = self.log_view.verticalScrollBar()
        at_bottom = scrollbar.value() >= (scrollbar.maximum() - 20)
        self.log_view.insertPlainText(content)
        if at_bottom:
            scrollbar.setValue(scrollbar.maximum())
