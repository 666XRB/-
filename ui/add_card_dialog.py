from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QTextEdit, 
                           QPushButton, QMessageBox, QFrame)
from PyQt6.QtCore import Qt
from models.knowledge_card import KnowledgeCard
from database.db_manager import DBManager
from PyQt6.QtGui import QIcon
import os
from PyQt6.QtWidgets import QComboBox  # 新增导入

class AddCardDialog(QDialog):
    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db_manager = db_manager
        self.setWindowTitle("添加知识卡片")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        # 获取资源路径
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icon_path = os.path.join(base_dir, 'resources', 'card.ico')
        self.arrow_path = os.path.join(base_dir, 'resources', 'down_arrow.png')  # 新增箭头图标路径
        
        # 简化样式表，只保留必要的样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
            }
            QComboBox, QLineEdit, QTextEdit {
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #d6d6d6;
                border-radius: 4px;
            }
        """)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 表单容器 - 移除灰色背景
        form_container = QFrame()
        form_container.setFrameShape(QFrame.Shape.NoFrame)  # 移除边框
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(0, 0, 0, 0)  # 移除内边距
        form_layout.setSpacing(12)
        form_layout.setSpacing(12)
        
        # 模块输入 - 修改为可编辑的下拉框
        self.module_label = QLabel("模块:")
        self.module_input = QComboBox()
        self.module_input.setEditable(True)
        self.module_input.addItems([
            "常识", "申论", "资料分析", 
            "判断推理", "公式", "规律", "随便记录"
        ])
        self.module_input.setCurrentIndex(-1)
        self.module_input.setMinimumWidth(300)  # 增加宽度
        
        # 设置下拉按钮样式 - 修改为使用系统默认箭头
        self.module_input.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #d6d6d6;
                border-radius: 4px;
            }
            QComboBox::drop-down {
                width: 25px;
                border-left: 1px solid #d6d6d6;
                border-radius: 0 4px 4px 0;
            }
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
        """)

        form_layout.addWidget(self.module_label)
        form_layout.addWidget(self.module_input)

        # 内容输入
        self.content_label = QLabel("内容:")
        self.content_input = QTextEdit()
        self.content_input.setMinimumHeight(120)
        form_layout.addWidget(self.content_label)
        form_layout.addWidget(self.content_input)

        # 记忆口诀输入
        self.mnemonic_label = QLabel("记忆口诀(可选):")
        self.mnemonic_input = QLineEdit()
        form_layout.addWidget(self.mnemonic_label)
        form_layout.addWidget(self.mnemonic_input)
        
        layout.addWidget(form_container)
        
        # 按钮布局
        button_container = QFrame()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        # 添加弹性空间使按钮靠右
        button_layout.addStretch()
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_card)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addWidget(button_container)

        self.setLayout(layout)
        
        # 设置对话框图标
        # 设置图标（使用相同路径处理方式）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'resources', 'card.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def save_card(self):
        """保存卡片到数据库"""
        module = self.module_input.currentText().strip()  # 修改这里：使用currentText()替代text()
        content = self.content_input.toPlainText().strip()
        mnemonic = self.mnemonic_input.text().strip() or None
        
        if not module or not content:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("警告")
            msg.setText("模块和内容不能为空!")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #000000;
                    font-size: 14px;
                }
            """)
            msg.exec()
            return

        # 创建新卡片并保存到数据库
        new_card = KnowledgeCard.create_new(module, content, mnemonic)
        try:
            self.db_manager.add_card(new_card)
            self.accept()  # 关闭对话框并返回成功
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存卡片失败: {str(e)}")