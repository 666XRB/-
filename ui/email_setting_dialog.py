from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, 
                           QMessageBox, QFormLayout, QComboBox)  # 改为使用QComboBox
from PyQt6.QtCore import Qt
import os
from PyQt6.QtGui import QIcon
from utils.email_manager import EmailManager

class EmailSettingDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("邮件设置")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.email_manager = EmailManager()
        # 修改历史记录相关变量
        self.max_history = 5  # 最大保存历史记录数
        self.email_history = []  # 历史记录列表
        
        self.init_ui()
        self.load_settings()  # 加载设置时会自动加载历史记录

    def init_ui(self):
        # 确保只设置一次布局
        if not self.layout():
            layout = QVBoxLayout(self)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)
            
            form_layout = QFormLayout()
            form_layout.setVerticalSpacing(12)
            
            # 发送邮箱输入
            self.sender_email = QLineEdit()
            self.sender_email.setPlaceholderText("例如: yourname@qq.com")
            form_layout.addRow("发送邮箱:", self.sender_email)
            
            # 授权码输入
            self.auth_code = QLineEdit()
            self.auth_code.setPlaceholderText("QQ邮箱需在设置中生成授权码")
            self.auth_code.setEchoMode(QLineEdit.EchoMode.Password)
            form_layout.addRow("授权码:", self.auth_code)
            
            # SMTP服务器
            self.smtp_server = QLineEdit()
            self.smtp_server.setPlaceholderText("例如: smtp.qq.com")
            form_layout.addRow("SMTP服务器:", self.smtp_server)
            
            # SMTP端口
            self.smtp_port = QLineEdit()
            self.smtp_port.setPlaceholderText("例如: 465(SSL)或587(TLS)")
            form_layout.addRow("SMTP端口:", self.smtp_port)
            
            # 接收邮箱 - 使用QComboBox并保持样式统一
            self.receiver_email = QComboBox()
            self.receiver_email.setEditable(True)
            self.receiver_email.setInsertPolicy(QComboBox.InsertPolicy.InsertAtTop)
            self.receiver_email.setDuplicatesEnabled(False)
            self.receiver_email.setStyleSheet("""
                QComboBox {
                    padding: 5px;
                    border: 1px solid #d6d6d6;
                    border-radius: 4px;
                    min-height: 25px;
                }
                QComboBox::drop-down {
                    width: 25px;
                    border-left: 1px solid #d6d6d6;
                }
            """)
            form_layout.addRow("接收邮箱:", self.receiver_email)
            
            layout.addLayout(form_layout)
            
            # 按钮布局 - 恢复原有优雅设计
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()
            
            # 测试连接按钮
            test_btn = QPushButton("测试连接")
            test_btn.setStyleSheet("""
                QPushButton {
                    min-width: 80px;
                    padding: 6px 12px;
                    background-color: #0078d7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
            test_btn.clicked.connect(self.test_connection)
            btn_layout.addWidget(test_btn)
            
            # 保存按钮
            save_btn = QPushButton("保存")
            save_btn.setStyleSheet(test_btn.styleSheet())
            save_btn.clicked.connect(self.save_settings)
            btn_layout.addWidget(save_btn)
            
            # 取消按钮
            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet(test_btn.styleSheet())
            cancel_btn.clicked.connect(self.reject)
            btn_layout.addWidget(cancel_btn)
            
            layout.addLayout(btn_layout)

    def load_settings(self):
        """加载已保存的邮件设置"""
        config = self.email_manager.load_config()
        if config:
            # 设置所有字段
            self.sender_email.setText(config.get('sender_email', ''))
            self.auth_code.setText(config.get('auth_code', ''))
            self.smtp_server.setText(config.get('smtp_server', 'smtp.qq.com'))
            self.smtp_port.setText(config.get('smtp_port', '465'))
            
            # 修改这里：使用setCurrentText()而不是setText()
            receiver_email = config.get('receiver_email', '')
            self.receiver_email.setCurrentText(receiver_email)
            
            # 加载历史记录
            if 'email_history' in config:
                self.email_history = config['email_history']
                self.receiver_email.clear()
                self.receiver_email.addItems(self.email_history)
                self.receiver_email.setCurrentText(receiver_email)

    def save_settings(self):
        """保存邮件设置"""
        config = {
            'sender_email': self.sender_email.text().strip(),
            'auth_code': self.auth_code.text().strip(),
            'smtp_server': self.smtp_server.text().strip(),
            'smtp_port': self.smtp_port.text().strip(),
            'receiver_email': self.receiver_email.currentText().strip()
        }
        
        # 验证必填项
        if not all([config['sender_email'], config['auth_code'], 
                   config['smtp_server'], config['smtp_port']]):
            QMessageBox.warning(self, "警告", "请填写所有必填项!")
            return
            
        # 更新历史记录
        current_email = config['receiver_email']
        if current_email:
            if current_email in self.email_history:
                self.email_history.remove(current_email)
            self.email_history.insert(0, current_email)
            self.email_history = self.email_history[:self.max_history]
            config['email_history'] = self.email_history
            
        if self.email_manager.save_config(config):
            QMessageBox.information(self, "成功", "邮件设置已保存!")
            self.accept()
            
    def test_connection(self):
        """测试SMTP连接"""
        from smtplib import SMTP_SSL, SMTP
        import ssl
        
        sender = self.sender_email.text().strip()
        auth_code = self.auth_code.text().strip()
        server = self.smtp_server.text().strip()
        port = self.smtp_port.text().strip()
        # 修改这里：使用currentText()而不是text()
        receiver = self.receiver_email.currentText().strip()
        
        if not all([sender, auth_code, server, port]):
            QMessageBox.warning(self, "警告", "请先填写完整的SMTP信息!")
            return
            
        try:
            port = int(port)
            if port == 465:  # SSL
                with SMTP_SSL(server, port) as smtp:
                    smtp.login(sender, auth_code)
            else:  # TLS
                with SMTP(server, port) as smtp:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.login(sender, auth_code)
                    
            # 连接成功后询问是否发送测试邮件
            reply = QMessageBox.information(
                self, 
                "成功", 
                "SMTP连接测试成功!\n是否要发送测试邮件?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.send_test_email()
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"SMTP连接失败: {str(e)}")
    
    def send_test_email(self):
        """发送测试邮件"""
        from smtplib import SMTP_SSL, SMTP, SMTPResponseException
        import ssl
        from email.mime.text import MIMEText
        
        sender = self.sender_email.text().strip()
        auth_code = self.auth_code.text().strip()
        server = self.smtp_server.text().strip()
        port = self.smtp_port.text().strip()
        # 修改这里：使用currentText()而不是text()
        receiver = self.receiver_email.currentText().strip()
        
        if not receiver:
            QMessageBox.warning(self, "警告", "请先填写接收邮箱!")
            return
            
        try:
            port = int(port)
            if port == 465:  # SSL
                with SMTP_SSL(server, port) as smtp:
                    smtp.login(sender, auth_code)
                    msg = MIMEText("哈喽~接下来可以在我这里发送知识卡片了！", 'plain', 'utf-8')
                    msg['From'] = sender
                    msg['To'] = receiver
                    msg['Subject'] = "知识卡片系统测试邮件"
                    smtp.sendmail(sender, receiver, msg.as_string())
            else:  # TLS
                with SMTP(server, port) as smtp:
                    smtp.starttls(context=ssl.create_default_context())
                    smtp.login(sender, auth_code)
                    msg = MIMEText("哈喽~接下来可以在我这里发送知识卡片了！", 'plain', 'utf-8')
                    msg['From'] = sender
                    msg['To'] = receiver
                    msg['Subject'] = "知识卡片系统测试邮件"
                    smtp.sendmail(sender, receiver, msg.as_string())
                    
            QMessageBox.information(self, "成功", "测试邮件已发送!")
        except SMTPResponseException as e:
            if e.smtp_code == -1 and e.smtp_error == b'\x00\x00\x00':
                # 特殊处理这个错误，认为邮件已发送成功
                QMessageBox.information(self, "成功", "测试邮件已发送!")
            else:
                QMessageBox.critical(self, "错误", f"发送测试邮件失败: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"发送测试邮件失败: {str(e)}")