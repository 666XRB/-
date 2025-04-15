from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QPushButton, 
                           QHBoxLayout, QMessageBox)
from PyQt6.QtCore import Qt
import os
from PyQt6.QtGui import QIcon

class SendCardsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("发送知识卡片")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # 设置图标
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        icon_path = os.path.join(base_dir, 'resources', 'card.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 按钮布局
        button_layout = QVBoxLayout()
        button_layout.setSpacing(12)
        
        # 创建按钮 (与导出PDF保持一致)
        self.today_button = QPushButton("发送今日卡片")
        self.week_button = QPushButton("发送本周卡片")
        self.all_button = QPushButton("发送全部卡片")
        self.select_button = QPushButton("选择日期发送")
        
        # 设置按钮样式
        for btn in [self.today_button, self.week_button, 
                   self.all_button, self.select_button]:
            btn.setStyleSheet("""
                QPushButton {
                    min-width: 200px;
                    padding: 8px 16px;
                    background-color: rgba(0, 120, 215, 0.9);
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 120, 215, 1);
                }
            """)
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)