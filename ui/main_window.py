import os
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLineEdit, QListWidget, 
                           QWidget, QAbstractItemView, QListWidgetItem,
                           QLabel, QFrame, QDialog, QTextEdit, QMessageBox)  # 添加 QDialog 和 QTextEdit
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, QSize  # 添加 QSize 导入
from PyQt6.QtCore import QPropertyAnimation
from PyQt6.QtGui import QColor
from PyQt6.QtGui import QColor, QFont, QIcon  # 添加QIcon导入
from database.db_manager import DBManager
from ui.add_card_dialog import AddCardDialog
from ui.edit_card_dialog import EditCardDialog
from utils.export_pdf import export_cards_to_pdf
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QCalendarWidget
from PyQt6.QtCore import QDate

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("知识库管理系统")  # 确保这个标题与FindWindow查找的一致
        self.setGeometry(100, 100, 800, 600)
        
        # 设置窗口图标
        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'card.ico')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
            else:
                print(f"警告: 图标文件未找到 - {icon_path}")
        except Exception as e:
            print(f"加载图标失败: {e}")
        self.db_manager = DBManager()
        self.init_ui()
    
    def init_ui(self):
        # 主窗口中心部件
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # 标题标签
        # 在init_ui方法中修改标题标签部分
        title_label = QLabel("知识卡片库 Developed by RunBoXu✨")
        title_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold;
            color: #0078d7;
            padding: 8px 0;
            border-bottom: 2px solid #0078d7;
            margin-bottom: 16px;
        """)
        layout.addWidget(title_label)
        
        # 搜索框
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("搜索模块或内容或者口诀...")
        self.search_box.textChanged.connect(self.search_cards)
        search_layout.addWidget(self.search_box)
        
        layout.addWidget(search_container)
        
        # 卡片列表容器
        list_container = QFrame()
        list_container.setFrameShape(QFrame.Shape.StyledPanel)
        list_layout = QVBoxLayout(list_container)
        list_layout.setContentsMargins(0, 0, 0, 0)
        
        self.card_list = QListWidget()
        self.card_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.card_list.setStyleSheet("""
            QListWidget::item:selected {
                background-color: #e5f1fb;
                border-left: 4px solid #0078d7;
            }
            QListWidget::item:hover {
                background-color: #e5f1fb;
                border-left: 2px solid #0078d7;
            }
        """)
        layout.addWidget(self.card_list)
        
        # 添加双击事件连接
        self.card_list.itemDoubleClicked.connect(self.preview_card)
        self.card_list.itemClicked.connect(self.on_item_clicked)
        list_layout.addWidget(self.card_list)
        
        layout.addWidget(list_container, stretch=1)
        
        # 按钮布局
        # 在init_ui方法中修改按钮部分
        button_container = QWidget()
        button_container.setStyleSheet("""
            background-color: rgba(255, 255, 255, 0.8);
            border-radius: 8px;
            padding: 8px;
        """)
        
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(16, 8, 16, 8)
        button_layout.setSpacing(12)
        
        # 添加按钮
        buttons = [
            ("添加卡片😄", self.add_card),
            ("编辑卡片🤔", self.edit_card),
            ("删除卡片😦", self.delete_card),
            ("导出PDF😍", self.export_pdf)
        ]
        
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    min-width: 80px;
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
                QPushButton:pressed {
                    background-color: rgba(0, 90, 158, 1);
                }
            """)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)
        
        layout.addWidget(button_container)
        
        self.setCentralWidget(central_widget)
        
        # 加载卡片数据
        self.load_cards()

    def preview_card(self, item):
        """预览卡片内容"""
        card_id = item.data(100)
        if not card_id:
            return
            
        # 增加查询次数
        self.db_manager.increment_query_count(card_id)
        
        card = self.db_manager.get_card_by_id(card_id)
        
        # 创建预览对话框
        preview_dialog = QDialog(self)
        preview_dialog.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QLabel, QTextEdit {
                color: #000000;
                background-color: #ffffff;
            }
        """)
        preview_dialog.setWindowTitle("卡片预览")
        preview_dialog.setMinimumWidth(500)
        
        # 移除原有的内联样式设置，改用统一样式表
        layout = QVBoxLayout(preview_dialog)
        
        # 模块标题
        title_label = QLabel(card.module)
        title_label.setProperty("class", "dialog-title")  # 使用样式类
        layout.addWidget(title_label)
        
        # 内容
        content_text = QTextEdit()
        content_text.setPlainText(card.content)
        content_text.setReadOnly(True)
        content_text.setProperty("class", "dialog-content")  # 使用样式类
        layout.addWidget(content_text)
        
        # 记忆口诀
        if card.mnemonic:
            mnemonic_label = QLabel(f"记忆口诀: {card.mnemonic}")
            mnemonic_label.setProperty("class", "dialog-mnemonic")
            layout.addWidget(mnemonic_label)
        
        # 底部信息
        footer_label = QLabel(f"创建时间: {card.created_at} | 更新时间: {card.updated_at} | 查询次数: {card.query_count}")
        footer_label.setProperty("class", "dialog-footer")
        layout.addWidget(footer_label)
        
        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(preview_dialog.close)
        layout.addWidget(close_button)
        
        preview_dialog.exec()
        
        # 移除自动刷新列表的代码
        # 现在只更新当前卡片的显示
        self.update_card_display(card_id)

    def load_cards(self):
        """加载所有卡片到列表"""
        # 保存当前滚动位置
        scroll_bar = self.card_list.verticalScrollBar()
        scroll_pos = scroll_bar.value()
        
        self.card_list.clear()
        cards = self.db_manager.get_all_cards()
        self.update_window_title(len(cards))
        for card in cards:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 120))
            
            # 主容器
            list_item = QWidget()
            layout = QVBoxLayout(list_item)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(4)
            
            # 标题区域 (必须存在)
            title_label = QLabel(card.module)
            title_label.setStyleSheet("""
                font-weight: bold;
                color: #0078d7;
                font-size: 15px;
                padding-bottom: 2px;
                margin: 0;
            """)
            layout.addWidget(title_label)
            
            # 内容区域 (必须存在)
            content_label = QLabel(card.content[:100] + "..." if len(card.content) > 100 else card.content)
            content_label.setStyleSheet("""
                color: #323130;
                font-size: 14px;
                padding: 0;
                margin: 0;
            """)
            content_label.setWordWrap(True)
            layout.addWidget(content_label)
            
            # 记忆口诀区域 (始终创建但可能隐藏)
            mnemonic_label = QLabel()
            mnemonic_label.setStyleSheet("""
                font-style: italic;
                color: #666666;
                font-size: 13px;
                padding: 2px 0 0 0;
                margin: 0;
            """)
            if card.mnemonic:
                mnemonic_label.setText(f"💡 {card.mnemonic[:50]}" + ("..." if len(card.mnemonic) > 50 else ""))
            else:
                mnemonic_label.hide()
            layout.addWidget(mnemonic_label)
            
            # 底部信息区域 (必须存在)
            footer_label = QLabel(f"📅 {card.created_at} | 🔍 {card.query_count}次")
            footer_label.setStyleSheet("""
                color: #797775;
                font-size: 11px;
                padding-top: 2px;
                margin: 0;
            """)
            layout.addWidget(footer_label)
            
            # 设置背景色
            base_color = self.get_color_by_query_count(card.query_count).name()
            list_item.setStyleSheet(f"""
                background-color: {base_color};
                border-radius: 4px;
                margin: 2px;
            """)
            
            item.setData(100, card.id)
            self.card_list.addItem(item)
            self.card_list.setItemWidget(item, list_item)
        
        # 恢复滚动位置
        scroll_bar.setValue(scroll_pos)
    
    def search_cards(self, query):
        """根据搜索词过滤卡片"""
        # 清空搜索框时恢复完整列表
        if not query.strip():
            self.load_cards()
            return
        
        # 保存当前滚动位置
        scroll_bar = self.card_list.verticalScrollBar()
        scroll_pos = scroll_bar.value()
        
        self.card_list.clear()
        cards = self.db_manager.search_cards(query)  # 这里会调用修改后的搜索方法
        self.update_window_title(len(cards))
        for card in cards:
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 120))
            
            # 主容器
            list_item = QWidget()
            layout = QVBoxLayout(list_item)
            layout.setContentsMargins(8, 8, 8, 8)
            layout.setSpacing(4)
            
            # 标题区域
            title_label = QLabel(card.module)
            title_label.setStyleSheet("""
                font-weight: bold;
                color: #0078d7;
                font-size: 15px;
                padding-bottom: 2px;
                margin: 0;
            """)
            layout.addWidget(title_label)
            
            # 内容区域
            content_label = QLabel(card.content[:100] + "..." if len(card.content) > 100 else card.content)
            content_label.setStyleSheet("""
                color: #323130;
                font-size: 14px;
                padding: 0;
                margin: 0;
            """)
            content_label.setWordWrap(True)
            layout.addWidget(content_label)
            
            # 记忆口诀区域
            if card.mnemonic:
                mnemonic_label = QLabel(f"💡 {card.mnemonic[:50]}" + ("..." if len(card.mnemonic) > 50 else ""))
                mnemonic_label.setStyleSheet("""
                    font-style: italic;
                    color: #666666;
                    font-size: 13px;
                    padding: 2px 0 0 0;
                    margin: 0;
                """)
                layout.addWidget(mnemonic_label)
            
            # 底部信息区域
            footer_label = QLabel(f"📅 {card.created_at} | 🔍 {card.query_count}次")
            footer_label.setStyleSheet("""
                color: #797775;
                font-size: 11px;
                padding-top: 2px;
                margin: 0;
            """)
            layout.addWidget(footer_label)
            
            # 设置背景色
            base_color = self.get_color_by_query_count(card.query_count).name()
            list_item.setStyleSheet(f"""
                background-color: {base_color};
                border-radius: 4px;
                margin: 2px;
            """)
            
            item.setData(100, card.id)
            self.card_list.addItem(item)
            self.card_list.setItemWidget(item, list_item)
        
        # 恢复滚动位置
        scroll_bar.setValue(scroll_pos)

    def get_color_by_query_count(self, query_count):
        """根据查询次数返回不同颜色(基于记忆曲线的优雅配色)"""
        if query_count == 0:
            return QColor("#f5f5f5")   # 浅灰色 - 未查询
        elif query_count < 5:
            return QColor("#e3f2fd")   # 淡蓝色 - 初始学习
        elif query_count < 10:
            return QColor("#bbdefb")   # 浅蓝色 - 短期记忆
        elif query_count < 20:
            return QColor("#90caf9")   # 中蓝色 - 记忆巩固
        elif query_count < 30:
            return QColor("#ffccbc")   # 浅橙色 - 中期记忆
        elif query_count < 50:
            return QColor("#ffab91")   # 中橙色 - 长期记忆
        elif query_count < 100:
            return QColor("#ff7043")   # 橙色 - 熟练掌握
        else:
            return QColor("#f4511e")   # 深橙色 - 完全掌握

    def add_card(self):
        dialog = AddCardDialog(self.db_manager)
        if dialog.exec():
            self.load_cards()
            self.update_window_title()
    
    def delete_card(self):
        selected_item = self.card_list.currentItem()
        if selected_item:
            card_id = selected_item.data(100)
            card = self.db_manager.get_card_by_id(card_id)
            
            # 创建自定义样式的确认对话框
            msg_box = QMessageBox(self)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #000000;
                }
            """)
            msg_box.setWindowTitle("确认删除")
            msg_box.setText(f'确定要删除卡片: "{card.module}" 吗?')
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #323130;
                }
            """)
            
            reply = msg_box.exec()
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.delete_card(card_id)
                # 检查搜索框是否有内容
                if self.search_box.text().strip():
                    self.search_cards(self.search_box.text())
                else:
                    self.load_cards()

    def edit_card(self):
        """打开编辑卡片对话框"""
        selected_item = self.card_list.currentItem()
        if selected_item:
            card_id = selected_item.data(100)
            dialog = EditCardDialog(self.db_manager, card_id)
            if dialog.exec():
                # 检查搜索框是否有内容
                if self.search_box.text().strip():
                    # 保持搜索状态
                    self.search_cards(self.search_box.text())
                else:
                    # 返回完整列表
                    self.load_cards()

    def delete_card(self):
        """删除选中卡片"""
        selected_item = self.card_list.currentItem()
        if selected_item:
            card_id = selected_item.data(100)
            card = self.db_manager.get_card_by_id(card_id)
            
            # 创建自定义样式的确认对话框
            msg_box = QMessageBox(self)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #000000;
                }
            """)
            msg_box.setWindowTitle("确认删除")
            msg_box.setText(f'确定要删除卡片: "{card.module}" 吗?')
            msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg_box.setStyleSheet("""
                QMessageBox {
                    background-color: #ffffff;
                }
                QLabel {
                    color: #323130;
                }
            """)
            
            reply = msg_box.exec()
            
            if reply == QMessageBox.StandardButton.Yes:
                self.db_manager.delete_card(card_id)
                # 检查搜索框是否有内容
                if self.search_box.text().strip():
                    self.search_cards(self.search_box.text())
                else:
                    self.load_cards()

    def export_pdf(self):
        dialog = ExportDialog(self)
        
        def export_handler(export_type):
            dialog.close()
            from utils.export_pdf import export_cards_to_pdf
            success, message = export_cards_to_pdf(self.db_manager.get_all_cards(), export_type)
            if success:
                QMessageBox.information(self, "导出成功", message)
            else:
                if "没有学习记录" in message:
                    QMessageBox.information(self, "提示", message)
                else:
                    QMessageBox.critical(self, "错误", message)
        
        # 连接按钮信号
        dialog.all_button.clicked.connect(lambda: export_handler("all"))
        dialog.today_button.clicked.connect(lambda: export_handler("today")) 
        dialog.week_button.clicked.connect(lambda: export_handler("week"))
        dialog.select_button.clicked.connect(lambda: self.export_selected_date(dialog))  # 连接选择导出按钮
        
        # 显示对话框
        dialog.exec()

    def on_item_clicked(self, item):
        # 不需要额外处理，选中状态由样式表控制
        pass

    def export_selected_date(self, dialog):
        """处理选择日期导出功能，支持多选并智能反馈"""
        from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                    QPushButton, QListWidget, QCalendarWidget)
        from PyQt6.QtCore import QDate, Qt
        
        date_dialog = QDialog(self)
        date_dialog.setWindowTitle("选择导出日期")
        date_dialog.resize(400, 500)
        layout = QVBoxLayout()
        
        # 日历控件
        calendar = QCalendarWidget()
        calendar.setMaximumDate(QDate.currentDate())
        
        # 日期列表
        date_list = QListWidget()
        
        # 添加/删除按钮
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("添加日期")
        remove_btn = QPushButton("删除选中")
        
        def add_date():
            selected = calendar.selectedDate()
            date_str = selected.toString("yyyy-MM-dd")
            items = date_list.findItems(date_str, Qt.MatchFlag.MatchExactly)
            if not items:
                date_list.addItem(date_str)
        
        def remove_date():
            for item in date_list.selectedItems():
                date_list.takeItem(date_list.row(item))
        
        add_btn.clicked.connect(add_date)
        remove_btn.clicked.connect(remove_date)
        
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        
        # 确定按钮
        ok_btn = QPushButton("确定导出")
        
        # 布局
        layout.addWidget(calendar)
        layout.addLayout(btn_layout)
        layout.addWidget(date_list)
        layout.addWidget(ok_btn)
        
        def export_selected():
            selected_dates = [
                QDate.fromString(item.text(), "yyyy-MM-dd").toPyDate()
                for item in date_list.findItems("", Qt.MatchFlag.MatchContains)
            ]
            
            success_dates = []
            empty_dates = []
            
            for date in selected_dates:
                success, message = export_cards_to_pdf(
                    self.db_manager.get_all_cards(),
                    export_type="custom",
                    selected_dates=[date]
                )
                if success:
                    success_dates.append(date.strftime("%m月%d日"))
                else:
                    empty_dates.append(date.strftime("%m月%d日"))
            
            # 构建反馈消息
            message = ""
            if success_dates:
                message += f"成功导出以下日期的卡片:\n{', '.join(success_dates)}\n\n"
            if empty_dates:
                message += f"以下日期没有学习记录:\n{', '.join(empty_dates)}"
            
            if not success_dates and not empty_dates:
                message = "没有选择任何日期"
            elif not success_dates:
                message = f"您选择的日期({', '.join(empty_dates)})都没有学习记录"
            
            QMessageBox.information(self, "导出结果", message)
            date_dialog.accept()
        
        ok_btn.clicked.connect(export_selected)
        date_dialog.setLayout(layout)
        date_dialog.exec()


    def update_window_title(self, count=None):
        """更新窗口标题显示卡片数量"""
        if count is None:
            count = len(self.db_manager.get_all_cards())
        self.setWindowTitle(f"知识库管理系统 - 共 {count} 张卡片")

    def update_card_display(self, card_id):
        """更新单个卡片的显示"""
        card = self.db_manager.get_card_by_id(card_id)
        if not card:
            return
        
        for i in range(self.card_list.count()):
            item = self.card_list.item(i)
            if item.data(100) == card_id:
                widget = self.card_list.itemWidget(item)
                
                # 查找所有子控件
                labels = widget.findChildren(QLabel)
                
                # 确保至少有3个标签(标题、内容、底部信息)
                if len(labels) < 3:
                    # 重建卡片内容
                    self.card_list.takeItem(i)
                    self.load_cards()
                    return
                
                # 更新标题
                labels[0].setText(card.module)
                
                # 更新内容
                labels[1].setText(card.content[:100] + "..." if len(card.content) > 100 else card.content)
                
                # 处理记忆口诀
                if len(labels) > 3:  # 有记忆口诀标签
                    if card.mnemonic:
                        labels[2].setText(f"💡 {card.mnemonic[:50]}" + ("..." if len(card.mnemonic) > 50 else ""))
                        labels[2].show()
                    else:
                        labels[2].hide()
                
                # 更新底部信息
                labels[-1].setText(f"📅 {card.created_at} | 🔍 {card.query_count}次")
                
                # 更新背景色
                base_color = self.get_color_by_query_count(card.query_count).name()
                widget.setStyleSheet(f"""
                    background-color: {base_color};
                    border-radius: 4px;
                    margin: 2px;
                """)

    def closeEvent(self, event):
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.conn.close()
        except Exception as e:
            print(f"关闭数据库连接时出错: {e}")
        event.accept()

class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出选项")
        layout = QVBoxLayout()
        
        self.button_layout = QVBoxLayout()
        
        self.all_button = QPushButton("导出全部")
        self.today_button = QPushButton("导出今天")
        self.week_button = QPushButton("导出本周")
        self.select_button = QPushButton("选择导出")  # 新增的选择导出按钮
        
        # 设置按钮样式
        for btn in [self.all_button, self.today_button, self.week_button, self.select_button]:
            btn.setStyleSheet("""
                QPushButton {
                    min-width: 120px;
                    padding: 8px;
                    margin: 4px;
                    background-color: #0078d7;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
        
        self.button_layout.addWidget(self.all_button)
        self.button_layout.addWidget(self.today_button)
        self.button_layout.addWidget(self.week_button)
        self.button_layout.addWidget(self.select_button)  # 添加选择导出按钮
        
        layout.addLayout(self.button_layout)
        self.setLayout(layout)

class DateSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择导出日期")
        layout = QVBoxLayout()
        
        self.calendar = QCalendarWidget()
        self.calendar.setMaximumDate(QDate.currentDate())
        layout.addWidget(self.calendar)
        
        self.ok_button = QPushButton("确定")
        self.ok_button.clicked.connect(self.accept)
        layout.addWidget(self.ok_button)
        
        self.setLayout(layout)
    
    def selected_date(self):
        return self.calendar.selectedDate().toPyDate()

