from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QWidget, QPushButton, 
                             QFrame, QLabel, QComboBox, QGraphicsOpacityEffect)
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve

class DebugPage(QFrame):
    """调试控制面板页面"""
    check_devices_clicked = Signal()
    restart_adb_clicked = Signal()
    clear_forward_clicked = Signal()
    release_adb_clicked = Signal(bool) # True 为释放（停止监控），False 为恢复监控
    check_responsive_clicked = Signal(str) # 发送选中的设备 ID

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
        debug_layout = QVBoxLayout(self)
        debug_layout.setContentsMargins(20, 20, 20, 20)
        debug_layout.setSpacing(20)

        debug_title = QLabel("ADB 快速调试控制台")
        debug_title.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        debug_layout.addWidget(debug_title)

        desc_label = QLabel("通过以下快捷操作可以解决大部分 ADB 连接或转发异常问题。")
        desc_label.setStyleSheet("color: #888888; font-size: 13px;")
        debug_layout.addWidget(desc_label)

        # --- 第一组：设备管理 ---
        device_group = QFrame()
        device_group.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3c3c3c;")
        device_layout = QVBoxLayout(device_group)
        device_layout.setContentsMargins(15, 15, 15, 15)
        
        device_title = QLabel("📱 设备管理与响应检测")
        device_title.setStyleSheet("color: #007acc; font-weight: bold; border: none; margin-bottom: 5px;")
        device_layout.addWidget(device_title)

        device_controls = QHBoxLayout()
        self.btn_check_devices = QPushButton("检测设备")
        self.device_selector = QComboBox()
        self.device_selector.setMinimumWidth(200)
        self.device_selector.setStyleSheet("""
            QComboBox { 
                background-color: #3e3e42; color: white; border: 1px solid #454545; 
                padding: 8px; border-radius: 4px; font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #3e3e42;
                color: white;
                selection-background-color: #007acc;
            }
        """)
        self.btn_check_responsive = QPushButton("响应检查")
        
        for widget in [self.btn_check_devices, self.device_selector, self.btn_check_responsive]:
            if isinstance(widget, QPushButton):
                widget.setFixedSize(130, 40)
                widget.setCursor(Qt.PointingHandCursor)
                widget.setStyleSheet("""
                    QPushButton { 
                        background-color: #3e3e42; color: #cccccc; border: 1px solid #454545; 
                        font-weight: bold; border-radius: 4px; 
                    }
                    QPushButton:hover { background-color: #007acc; color: white; border: 1px solid #007acc; }
                """)
            device_controls.addWidget(widget)
        device_controls.addStretch()
        device_layout.addLayout(device_controls)
        debug_layout.addWidget(device_group)

        # --- 第二组：ADB 系统操作 ---
        adb_group = QFrame()
        adb_group.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3c3c3c;")
        adb_layout = QVBoxLayout(adb_group)
        adb_layout.setContentsMargins(15, 15, 15, 15)

        adb_title = QLabel("⚙️ ADB 系统维护")
        adb_title.setStyleSheet("color: #e6a23c; font-weight: bold; border: none; margin-bottom: 5px;")
        adb_layout.addWidget(adb_title)

        adb_controls = QHBoxLayout()
        self.btn_restart_adb = QPushButton("重启 ADB")
        self.btn_clear_forward = QPushButton("清理转发")
        self.btn_toggle_monitoring = QPushButton("停止监控 (释放资源)")
        self.btn_toggle_monitoring.setCheckable(True)
        
        for btn in [self.btn_restart_adb, self.btn_clear_forward, self.btn_toggle_monitoring]:
            btn.setFixedSize(140, 40)
            btn.setCursor(Qt.PointingHandCursor)
            
            if btn == self.btn_toggle_monitoring:
                btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #3e3e42; color: #cccccc; border: 1px solid #454545; 
                        font-weight: bold; border-radius: 4px; 
                    }
                    QPushButton:checked { background-color: #d13438; color: white; border: 1px solid #d13438; }
                    QPushButton:hover { background-color: #4e4e52; }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton { 
                        background-color: #3e3e42; color: #cccccc; border: 1px solid #454545; 
                        font-weight: bold; border-radius: 4px; 
                    }
                    QPushButton:hover { background-color: #d13438; color: white; border: 1px solid #d13438; }
                """)
            adb_controls.addWidget(btn)
        adb_controls.addStretch()
        adb_layout.addLayout(adb_controls)
        debug_layout.addWidget(adb_group)
        
        # 状态提示区
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #569cd6; font-family: 'Consolas';")
        debug_layout.addWidget(self.status_label)
        
        # --- 引导说明 ---
        guide_container = QFrame()
        guide_container.setStyleSheet("background-color: #252526; border-radius: 8px; border: 1px solid #3c3c3c;")
        guide_layout = QVBoxLayout(guide_container)
        guide_layout.setContentsMargins(20, 20, 20, 20)
        guide_layout.setSpacing(15)

        guide_title = QLabel("💡 操作引导与故障排除")
        guide_title.setStyleSheet("color: #007acc; font-size: 15px; font-weight: bold; border: none;")
        guide_layout.addWidget(guide_title)

        self.add_guide_item(guide_layout, "1. 为什么检测不到设备？", 
                       "请确保手机已通过 USB 连接电脑，并开启了【开发者选项】中的【USB 调试】。")
        self.add_guide_item(guide_layout, "2. 列表刷不出来页面？", 
                       "请确认手机 App 已经打开了 WebView 页面。如果仍未显示，请尝试点击下方的【重启 ADB】。")
        self.add_guide_item(guide_layout, "3. 如何让 Edge/Chrome 重新看到设备？", 
                       "由于本工具会持续占用 ADB 调试端口进行自动转发，如果您需要使用浏览器自带的 inspect 功能，请点击下方的【停止监控】按钮释放资源。")

        debug_layout.addWidget(guide_container)
        debug_layout.addStretch()

        # 绑定事件
        self.btn_check_devices.clicked.connect(self.check_devices_clicked.emit)
        self.btn_restart_adb.clicked.connect(self.restart_adb_clicked.emit)
        self.btn_clear_forward.clicked.connect(self.clear_forward_clicked.emit)
        self.btn_toggle_monitoring.clicked.connect(self.on_toggle_monitoring)
        self.btn_check_responsive.clicked.connect(lambda: self.check_responsive_clicked.emit(self.device_selector.currentText()))

    def on_toggle_monitoring(self):
        is_released = self.btn_toggle_monitoring.isChecked()
        if is_released:
            self.btn_toggle_monitoring.setText("恢复监控 (重新捕获)")
            self.status_label.setText("监控已停止，ADB 资源已释放")
        else:
            self.btn_toggle_monitoring.setText("停止监控 (释放资源)")
            self.status_label.setText("监控中...")
        self.release_adb_clicked.emit(is_released)

    def add_guide_item(self, layout, title, desc):
        item_layout = QVBoxLayout()
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #cccccc; font-weight: bold; border: none;")
        d_label = QLabel(desc)
        d_label.setStyleSheet("color: #888888; font-size: 12px; border: none;")
        d_label.setWordWrap(True)
        item_layout.addWidget(t_label)
        item_layout.addWidget(d_label)
        layout.addLayout(item_layout)

    def update_devices(self, devices):
        current = self.device_selector.currentText()
        self.device_selector.clear()
        self.device_selector.addItems(devices)
        if current in devices:
            self.device_selector.setCurrentText(current)

    def set_status(self, text):
        self.status_label.setText(text)

    def set_buttons_enabled(self, enabled):
        self.btn_check_devices.setEnabled(enabled)
        self.btn_restart_adb.setEnabled(enabled)
        self.btn_clear_forward.setEnabled(enabled)
        self.btn_check_responsive.setEnabled(enabled)
        self.btn_toggle_monitoring.setEnabled(enabled)
