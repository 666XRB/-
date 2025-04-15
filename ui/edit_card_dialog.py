from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                           QLabel, QLineEdit, QTextEdit,
                           QPushButton, QMessageBox)
from database.db_manager import DBManager
from models.knowledge_card import KnowledgeCard
import os
from PyQt6.QtGui import QIcon

class EditCardDialog(QDialog):
    def __init__(self, db_manager: DBManager, card_id: int):
        super().__init__()
        self.db_manager = db_manager
        self.card_id = card_id
        self.setWindowTitle("编辑知识卡片")
        self.setModal(True)
        # 修改这里：设置对话框宽度为原来的1.2倍
        self.setMinimumWidth(480)  # 原宽度400 * 1.2 = 480
        
        # 添加对话框基础样式
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel {
                color: #000000;
                font-size: 14px;
            }
            QLineEdit, QTextEdit {
                background-color: #ffffff;
                color: #000000;  /* 确保文字为纯黑色 */
                border: 1px solid #d6d6d6;
            }
        """)
        # 设置图标（修改为使用绝对路径）
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'resources', 'card.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        else:
            print(f"警告: 图标文件未找到 - {icon_path}")
        self.init_ui()
        self.load_card_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # 模块输入
        self.module_label = QLabel("模块:")
        self.module_input = QLineEdit()
        layout.addWidget(self.module_label)
        layout.addWidget(self.module_input)

        # 内容输入
        self.content_label = QLabel("内容:")
        self.content_input = QTextEdit()
        layout.addWidget(self.content_label)
        layout.addWidget(self.content_input)

        # 记忆口诀输入
        self.mnemonic_label = QLabel("记忆口诀(可选):")
        self.mnemonic_input = QLineEdit()
        layout.addWidget(self.mnemonic_label)
        layout.addWidget(self.mnemonic_input)

        # 按钮布局
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self.save_card)
        button_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("取消")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def load_card_data(self):
        """加载要编辑的卡片数据"""
        card = self.db_manager.get_card_by_id(self.card_id)
        if card:
            self.module_input.setText(card.module)
            self.content_input.setPlainText(card.content)
            self.mnemonic_input.setText(card.mnemonic or "")

    def save_card(self):
        """保存编辑后的卡片"""
        module = self.module_input.text().strip()
        content = self.content_input.toPlainText().strip()
        mnemonic = self.mnemonic_input.text().strip() or None

        if not module or not content:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)  # 修改这里
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

        # 获取当前卡片数据并更新
        card = self.db_manager.get_card_by_id(self.card_id)
        if card:
            card.update(module, content, mnemonic)
            try:
                self.db_manager.update_card(card)
                self.accept()  # 关闭对话框并返回成功
            except Exception as e:
                QMessageBox.critical(self, "错误", f"更新卡片失败: {str(e)}")
        else:
            QMessageBox.critical(self, "错误", "找不到要编辑的卡片!")