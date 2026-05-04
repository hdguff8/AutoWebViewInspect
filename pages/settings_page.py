from PySide6.QtWidgets import (QVBoxLayout, QWidget, QFrame, QLabel, 
                             QRadioButton, QButtonGroup, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve

class SettingsPage(QFrame):
    """系统设置页面"""
    adb_mode_changed = Signal(bool) # True for builtin, False for system

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: #1e1e1e;")
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
        settings_layout = QVBoxLayout(self)
        settings_layout.setContentsMargins(30, 30, 30, 30)
        settings_layout.setSpacing(20)

        settings_title = QLabel("系统设置")
        settings_title.setStyleSheet("color: white; font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        settings_layout.addWidget(settings_title)

        self.settings_container = QFrame()
        self.settings_container.setStyleSheet("background-color: #252526; border-radius: 12px; border: 1px solid #3c3c3c;")
        container_layout = QVBoxLayout(self.settings_container)
        container_layout.setContentsMargins(25, 25, 25, 25)
        container_layout.setSpacing(25)

        # 1. ADB 运行模式
        adb_section = QVBoxLayout()
        adb_label = QLabel("ADB 运行模式")
        adb_label.setStyleSheet("color: #007acc; font-size: 16px; font-weight: bold; border: none;")
        adb_section.addWidget(adb_label)

        self.adb_btn_group = QButtonGroup(self)
        self.radio_builtin = QRadioButton("使用程序内置 ADB (推荐)")
        self.radio_system = QRadioButton("使用系统环境变量中的 ADB")
        
        radio_style = """
            QRadioButton { color: #cccccc; font-size: 14px; padding: 10px; border-radius: 4px; border: none; }
            QRadioButton:hover { background-color: #2d2d30; }
            QRadioButton::indicator { width: 18px; height: 18px; }
            QRadioButton::indicator:unchecked { border: 2px solid #555; border-radius: 11px; background: none; }
            QRadioButton::indicator:checked { border: 2px solid #007acc; border-radius: 11px; background-color: #007acc; }
        """

        for radio in [self.radio_builtin, self.radio_system]:
            radio.setStyleSheet(radio_style)
            radio.setCursor(Qt.PointingHandCursor)
            adb_section.addWidget(radio)
            self.adb_btn_group.addButton(radio)
        
        container_layout.addLayout(adb_section)

        self.settings_status = QLabel("")
        self.settings_status.setStyleSheet("color: #4ec9b0; font-size: 13px; font-weight: bold; border: none;")
        container_layout.addWidget(self.settings_status)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #3c3c3c; max-height: 1px; border: none;")
        container_layout.addWidget(line)

        # 3. 冲突提示
        conflict_layout = QVBoxLayout()
        hint_title = QLabel("⚠️ 关于 ADB 版本冲突的说明")
        hint_title.setStyleSheet("color: #e6a23c; font-weight: bold; font-size: 14px; border: none;")
        hint_desc = QLabel("当电脑中存在多个版本的 ADB 时，可能会出现冲突。建议优先使用内置版本。")
        hint_desc.setStyleSheet("color: #aaaaaa; font-size: 12px; border: none; line-height: 1.5;")
        hint_desc.setWordWrap(True)
        
        conflict_layout.addWidget(hint_title)
        conflict_layout.addWidget(hint_desc)
        container_layout.addLayout(conflict_layout)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #3c3c3c; max-height: 1px; border: none;")
        container_layout.addWidget(line2)

        # 4. 系统信息
        info_layout = QVBoxLayout()
        self.version_label = QLabel("系统版本: v0.1.0")
        self.version_label.setStyleSheet("color: #888888; font-size: 13px; border: none;")
        info_layout.addWidget(self.version_label)
        container_layout.addLayout(info_layout)

        settings_layout.addWidget(self.settings_container)
        settings_layout.addStretch()

        self.radio_builtin.setChecked(True)
        self.adb_btn_group.buttonClicked.connect(lambda btn: self.adb_mode_changed.emit(btn == self.radio_builtin))

    def set_status(self, text):
        self.settings_status.setText(text)

    def set_version(self, version):
        self.version_label.setText(f"系统版本: {version}")
