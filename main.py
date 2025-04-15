import os
import sys
import ctypes
import datetime
from datetime import timedelta
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu, QLineEdit
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtNetwork import QLocalSocket, QLocalServer
from PyQt6.QtCore import QObject, pyqtSignal
from ui.main_window import MainWindow
from importlib.util import find_spec
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl
from utils.email_manager import EmailManager
from ui.email_setting_dialog import EmailSettingDialog
from ui.send_cards_dialog import SendCardsDialog
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
class AppSignals(QObject):
    show_window = pyqtSignal()
    quit_app = pyqtSignal()

def load_stylesheet():
    """加载样式表"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        styles_path = os.path.join(base_dir, "styles", "styles.qss")
        with open(styles_path, "r", encoding="utf-8") as f:
            stylesheet = f.read()
            # 验证样式表内容
            if not stylesheet.strip():
                print("警告: 样式表文件为空")
                return ""
            # 检查常见语法错误
            if stylesheet.count("/*") != stylesheet.count("*/"):
                print("警告: 样式表注释未闭合")
                return ""
            # 检查大括号匹配（更严格的检查）
            open_braces = stylesheet.count("{")
            close_braces = stylesheet.count("}")
            if open_braces != close_braces:
                print(f"警告: 样式表括号不匹配 ({{:{open_braces}, }}:{close_braces})")
                return ""
            return stylesheet
    except FileNotFoundError:
        print("警告: 未找到样式表文件")
        return ""
    except Exception as e:
        print(f"样式表解析错误: {e}")
        return ""

def is_already_running():
    """使用Windows Mutex检查是否已有实例在运行"""
    mutex_name = "KnowledgeBaseApp_Mutex"
    mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    
    if last_error == 183:  # ERROR_ALREADY_EXISTS
        # 查找并激活已有窗口
        hwnd = ctypes.windll.user32.FindWindowW(None, "知识库管理系统")
        if hwnd:
            # 恢复窗口（如果最小化）
            ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
            # 激活窗口
            ctypes.windll.user32.SetForegroundWindow(hwnd)
        return True
    return False

def check_autostart():
    """检查是否已设置开机自启动(注册表方式)"""
    try:
        import winreg
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_READ
            )
            try:
                winreg.QueryValueEx(key, "知识卡片系统")
                return True
            except WindowsError:
                return False
            finally:
                winreg.CloseKey(key)
        except Exception as e:
            print(f"检查自启动时出错: {e}")
            return False
    except ImportError:
        print("无法导入winreg模块")
        return False

def toggle_autostart(checked, action=None):
    """切换开机自启动状态(使用注册表方式)"""
    try:
        import winreg
    except ImportError:
        QMessageBox.critical(
            None,
            "错误",
            "无法访问Windows注册表"
        )
        if action:
            action.setChecked(not checked)
        return False
    
    # 获取程序路径
    app_path = sys.executable if getattr(sys, 'frozen', False) else __file__
    
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        
        if checked:
            # 添加开机启动项
            winreg.SetValueEx(
                key, 
                "知识卡片系统", 
                0,
                winreg.REG_SZ,
                f'"{app_path}"'
            )
        else:
            # 删除开机启动项
            try:
                winreg.DeleteValue(key, "知识卡片系统")
            except WindowsError:
                pass
            
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        QMessageBox.warning(
            None,
            "错误",
            f"修改自启动设置失败: {str(e)}"
        )
        if action:
            action.setChecked(not checked)
        return False
class AutoSender:
    def __init__(self, window):
        self.window = window
        self.timer = QTimer()
        self.timer.timeout.connect(self._on_timer_timeout)  # 修改为内部处理函数
        self.is_active = True
        self.next_send_time = None
        self.is_sending = False
        self.auto_send_action = None
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_menu_text)
        self.update_timer.start(1000)
        
        
        # 初始化时立即发送一次
        self._send_auto_cards()
        # 启动定时器(2分钟测试)
        self._start_timer()

        # 新增周日检测定时器
        # 优化后的周日检测定时器
        self.sunday_timer = QTimer()
        self.sunday_timer.timeout.connect(self._check_sunday_time)
        self._adjust_sunday_timer_interval()  # 初始设置合理间隔

    def _start_timer(self):
        """启动定时器"""
        self.timer.start(120000)  # 2分钟
        self.next_send_time = datetime.datetime.now() + datetime.timedelta(milliseconds=120000)

    def _on_timer_timeout(self):
        """定时器超时处理"""
        if self.is_active:
            self._send_auto_cards()
            # 重置定时器
            self._start_timer()

    def update_menu_text(self):
        """更新菜单文本显示状态"""
        if not hasattr(self, 'auto_send_action') or not self.auto_send_action:
            return
        status_text = self.get_next_send_text()
        self.auto_send_action.setText(f"定时发送 ({status_text})")

    def toggle_auto_send(self, checked):
        """切换自动发送状态"""
        self.is_active = checked
        if checked:
            # 立即发送一次
            self._send_auto_cards()
            # 启动定时器
            self._start_timer()
        else:
            self.timer.stop()
            self.next_send_time = None

    def _send_auto_cards(self):
        """执行自动发送(内部方法)"""
        if self.is_sending:
            return
            
        self.is_sending = True
        try:
            cards = self.window.db_manager.get_today_cards()
            
            if not cards:
                # 如果没有卡片，发送提醒邮件
                subject = "快点去学习啊！笨蛋！"
                content = """
                <!DOCTYPE html>
                <html>
                <body>
                <h2>再不学习明年你就得继续学，还不如一年学习</h2>
                <p>该学习的时候学习啊！而且这是国考啊，机会难得，错过再也没有了</p>
                </body>
                </html>
                """
                result = send_email(content, subject, silent=True)
                log_msg = f"[{datetime.datetime.now()}] 发送学习提醒 {'成功' if result else '失败'}"
                print(log_msg)
                return
                
            html_content = convert_cards_to_html(cards)
            subject = f"{datetime.datetime.now().strftime('%Y-%m-%d')} 知识卡片(自动发送)"
            result = send_email(html_content, subject, silent=True)
            
            # 记录日志
            log_msg = f"[{datetime.datetime.now()}] 自动发送 {'成功' if result else '失败'}"
            print(log_msg)
            
        except Exception as e:
            print(f"自动发送失败: {e}")
        finally:
            self.is_sending = False
            self.update_menu_text()

    def _start_timer(self):
        """启动定时器"""
        self.timer.start(3600000)  # 修改为1小时(3600000毫秒)
        self.next_send_time = datetime.datetime.now() + datetime.timedelta(milliseconds=3600000)

    def get_next_send_text(self):
        """获取下次发送时间的提示文本"""
        if not self.is_active:
            return "定时发送已关闭"
            
        if self.next_send_time is None:
            return "定时发送准备中..."
            
        remaining = (self.next_send_time - datetime.datetime.now()).total_seconds()
        if remaining <= 0:
            return "正在发送..."
            
        hours = int(remaining // 3600)
        minutes = int((remaining % 3600) // 60)
        seconds = int(remaining % 60)
        return f"下次发送: {hours:02d}:{minutes:02d}:{seconds:02d}"


    def _adjust_sunday_timer_interval(self):
        """动态调整定时器间隔以优化性能"""
        now = datetime.datetime.now()
        # 如果是周日且接近下午2点(1小时内)，则每分钟检查
        if now.weekday() == 6 and now.hour == 13 and now.minute >= 0:
            interval = 60000  # 1分钟
        # 其他时间每小时检查一次
        else:
            interval = 3600000  # 1小时
        self.sunday_timer.setInterval(interval)
        
    def _check_sunday_time(self):
        """检查是否是周日下午2点"""
        now = datetime.datetime.now()
        if now.weekday() == 6 and now.hour == 14 and now.minute == 0:
            self._send_forget_cards_silently()
        # 每次检查后重新调整定时器间隔
        self._adjust_sunday_timer_interval()
def main():
    if is_already_running():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("程序已在运行中")
        msg.setWindowTitle("提示")
        msg.exec()
        return
    
    app = QApplication(sys.argv)
    
    # 设置应用程序用户模型ID(AppUserModelID)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("KnowledgeBaseApp")
    except Exception as e:
        print(f"设置AppUserModelID失败: {e}")
    
    # 设置应用图标
    icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'card.ico')
    try:
        app_icon = QIcon(icon_path)
    except Exception as e:
        print(f"加载图标失败: {e}")
        app_icon = QIcon()
    
    # 创建信号对象
    signals = AppSignals()
    
    # 创建主窗口
    window = MainWindow()
    window.setWindowIcon(app_icon)
    
    # 创建自动发送器
    auto_sender = AutoSender(window)  # 将auto_sender的创建移到main函数内部

    # 添加全局快捷键 CTRL+G 显示/隐藏窗口
    show_shortcut = QShortcut(QKeySequence("Ctrl+G"), window)
    show_shortcut.activated.connect(lambda: (
        print("[测试] 检测到Ctrl+G快捷键按下"),
        window.hide() if window.isVisible() else (
            window.showNormal(),
            window.activateWindow(),
            window.raise_()
        )
    ))

    # 添加备用全局快捷键 CTRL+ALT+G
    backup_shortcut = QShortcut(QKeySequence("Ctrl+Alt+G"), window)
    backup_shortcut.activated.connect(lambda: (
        print("[测试] 检测到Ctrl+Alt+G快捷键按下"),
        window.hide() if window.isVisible() else (
            window.showNormal(),
            window.activateWindow(),
            window.raise_()
        )
    ))
    # 添加快速添加卡片快捷键 CTRL+J
    add_card_shortcut = QShortcut(QKeySequence("Ctrl+J"), window)
    add_card_shortcut.activated.connect(lambda: (
        print("[测试] 检测到Ctrl+J快捷键按下"),
        window.showNormal(),
        window.activateWindow(),
        window.raise_(),
        window.add_card()  # 直接调用主窗口的添加卡片方法
    ))

    # 添加备用快速添加卡片快捷键 CTRL+ALT+J
    add_card_backup_shortcut = QShortcut(QKeySequence("Ctrl+Alt+J"), window)
    add_card_backup_shortcut.activated.connect(lambda: (
        print("[测试] 检测到Ctrl+Alt+J快捷键按下"),
        window.showNormal(),
        window.activateWindow(),
        window.raise_(),
        window.add_card()  # 直接调用主窗口的添加卡片方法
    ))
    # 添加快速导出PDF快捷键 CTRL+P
    export_pdf_shortcut = QShortcut(QKeySequence("Ctrl+P"), window)
    export_pdf_shortcut.activated.connect(lambda: (
        print("[测试] 检测到Ctrl+P快捷键按下"),
        window.showNormal(),
        window.activateWindow(),
        window.raise_(),
        window.export_pdf()  # 直接调用主窗口的导出PDF方法
    ))

    # 添加备用快速导出PDF快捷键 CTRL+ALT+P
    export_pdf_backup_shortcut = QShortcut(QKeySequence("Ctrl+Alt+P"), window)
    export_pdf_backup_shortcut.activated.connect(lambda: (
        print("[测试] 检测到Ctrl+Alt+P快捷键按下"),
        window.showNormal(),
        window.activateWindow(),
        window.raise_(),
        window.export_pdf()  # 直接调用主窗口的导出PDF方法
    ))





    # 创建系统托盘
    global tray
    if QSystemTrayIcon.isSystemTrayAvailable():
        tray = QSystemTrayIcon()
        try:
            tray.setIcon(app_icon)
        except:
            pass
        tray.setToolTip("知识卡片系统")
        
        # 添加左键点击事件
        def on_tray_clicked(reason):
            if reason == QSystemTrayIcon.ActivationReason.Trigger:
                window.showNormal()
                window.activateWindow()
        
        tray.activated.connect(on_tray_clicked)
        
        # 创建托盘菜单部分
        menu = QMenu()
        
        # 1. 定义所有QAction对象
        mail_action = QAction("邮箱配置")
        help_action = QAction("帮助") 
        music_action = QAction("听歌放松")
        show_action = QAction("显示主窗口")
        autostart_action = QAction("开机自启动")
        autostart_action.setCheckable(True)
        autostart_action.setChecked(check_autostart())
        quit_action = QAction("退出")
        shortcut_hint = QAction("显示窗口快捷键: Ctrl+G / Ctrl+Alt+G")
        shortcut_add=QAction("快速添加卡片: Ctrl+J / Ctrl+Alt+J")
        shortcut_export = QAction("快速导出PDF: Ctrl+P / Ctrl+Alt+P")  # 新增导出快捷键提示
        shortcut_add.setEnabled(False)
        shortcut_hint.setEnabled(False)  # 设置为不可点击
        shortcut_export.setEnabled(False)  # 设置为不可点击
        # menu.insertAction(menu.actions()[0], shortcut_hint)  # 添加到菜单顶部
        menu.addAction(shortcut_hint)
        menu.addAction(shortcut_add)
        menu.addAction(shortcut_export)  # 添加到菜单
        # 2. 创建发送卡片子菜单
        send_menu = QMenu("发送卡片")
        send_action = QAction("手动发送")
        auto_send_action = QAction("定时发送")
        auto_send_action.setCheckable(True)
        auto_send_action.setChecked(True)  # 默认选中
        auto_send_action.toggled.connect(auto_sender.toggle_auto_send)
        auto_sender.auto_send_action = auto_send_action
        
        # 3. 关于菜单
        about_menu = QMenu("关于")
        clear_action = QAction("清空卡片")
        about_author_action = QAction("关于作者")
        
        # 4. 按指定顺序添加菜单项
        menu.addAction(mail_action)  # 邮件设置
        menu.addMenu(send_menu)      # 发送卡片子菜单
        send_menu.addAction(send_action)  # 手动发送
        send_menu.addSeparator()
        send_menu.addAction(auto_send_action)  # 定时发送
        # 1. 在托盘菜单创建部分添加新的action
        forget_action = QAction("易忘卡片")
        
        # 2. 在send_menu子菜单中添加这个action
        send_menu.addAction(forget_action)
        
        # 3. 连接信号
        forget_action.triggered.connect(lambda: send_forget_cards(window))
        
        menu.addSeparator()  # 第一个分割线
        menu.addAction(help_action)  # 帮助
        
        menu.addSeparator()  # 第二个分割线
        menu.addAction(music_action)  # 听歌放松
        
        menu.addSeparator()  # 第三个分割线
        menu.addAction(show_action)  # 显示主窗口
        menu.addAction(autostart_action)  # 开机自启动
        
        # 关于菜单
        about_menu.addAction(clear_action)  # 清空卡片
        about_menu.addAction(about_author_action)  # 关于作者
        menu.addMenu(about_menu)  # 关于
        
        menu.addSeparator()  # 第四个分割线
        menu.addAction(quit_action)  # 退出
        
        # 连接信号
        mail_action.triggered.connect(lambda: show_email_settings())
        send_action.triggered.connect(lambda: send_daily_cards(window))
        help_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("https://wx.mail.qq.com/list/readtemplate?name=app_intro.html#/agreement/authorizationCode")))
        music_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("http://jay.xurunbo.top")))
        show_action.triggered.connect(window.showNormal)
        autostart_action.triggered.connect(lambda checked: toggle_autostart(checked, autostart_action))
        clear_action.triggered.connect(lambda: show_clear_confirmation(window))
        quit_action.triggered.connect(app.quit)
        about_author_action.triggered.connect(lambda: QDesktopServices.openUrl(QUrl("http://xurunbo.top/music")))
        # 按指定顺序添加到菜单
        menu.addAction(mail_action)
        # menu.addAction(send_action)
        menu.addAction(help_action)
        menu.addSeparator()
        menu.addAction(music_action)
        menu.addSeparator()
        menu.addAction(show_action)
        menu.addAction(autostart_action)
        about_menu.addAction(clear_action)
        about_menu.addAction(about_author_action)  # 添加到关于菜单中
        menu.addSeparator()
        menu.addAction(quit_action)
        
        tray.setContextMenu(menu)
        tray.show()

        # 只保留这一处关闭事件处理
        def on_close(event):
            window.hide()
            tray.showMessage(
                "知识卡片系统",
                "程序已最小化到托盘",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
            event.ignore()
        
        window.closeEvent = on_close
        
        # 设置默认字体
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)
        
        # 加载样式表
        stylesheet = load_stylesheet()
        if stylesheet:
            app.setStyleSheet(stylesheet)
        
        window.show()
        sys.exit(app.exec())

def show_clear_confirmation(window):
    """显示清空卡片的确认对话框，需要用户输入特定文字确认"""
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle("警告⚠️")
    
    # 创建自定义布局
    msg.setText("请确认清空所有卡片操作")  # 主提示文字
    msg.setInformativeText("请在下方输入框中输入：\"确定清空所有卡片\"")  # 详细说明
    
    # 创建输入框并设置最小宽度
    input_box = QLineEdit()
    input_box.setMinimumWidth(300)
    
    # 获取消息框布局并添加输入框
    layout = msg.layout()
    layout.addWidget(input_box, 2, 0, 1, 2)  # 将输入框放在第三行
    
    msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
    msg.setDefaultButton(QMessageBox.StandardButton.No)
    
    if msg.exec() == QMessageBox.StandardButton.Yes:
        # 检查输入内容是否完全匹配
        if input_box.text().strip() == "确定清空所有卡片":
            try:
                # 添加数据库管理器检查
                if not hasattr(window, 'db_manager'):
                    raise AttributeError("找不到数据库管理器")
                if not hasattr(window.db_manager, 'clear_all_cards'):
                    raise AttributeError("数据库管理器缺少clear_all_cards方法")
                if not hasattr(window, 'load_cards'):
                    raise AttributeError("主窗口缺少load_cards方法")
                
                # 执行清空操作
                window.db_manager.clear_all_cards()
                # 刷新卡片列表
                window.load_cards()
                
                QMessageBox.information(
                    None,
                    "完成",
                    "所有知识卡片已清空",
                    QMessageBox.StandardButton.Ok
                )
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "错误",
                    f"清空卡片失败: {str(e)}"
                )
        else:
            QMessageBox.warning(
                None,
                "警告",
                "输入内容不匹配，操作已取消",
                QMessageBox.StandardButton.Ok
            )

# 修改邮件设置函数定义 (移除self参数)
def show_email_settings():
    dialog = EmailSettingDialog()
    dialog.exec()

def send_daily_cards(window):
    """发送卡片功能"""
    dialog = SendCardsDialog(window)
    
    def convert_cards_to_html(cards):
        """将卡片转换为HTML格式"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>知识卡片</title>
            <style>
                body { font-family: 'Microsoft YaHei', sans-serif; }
                .card { 
                    border: 1px solid #0078d7;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                }
                .card-rare { background-color: #e6f7ff; }
                .card-common { background-color: #f6ffed; }
                .card-frequent { background-color: #fff7e6; }
                .module { 
                    color: #0078d7;
                    font-weight: bold;
                    font-size: 16px;
                }
                .content { margin: 10px 0; }
                .mnemonic { 
                    color: #ff0000;  /* 修改为红色 */
                    font-style: italic;
                }
                .card-info {
                    font-size: 12px;
                    color: #888;
                    margin-bottom: 5px;
                }
            </style>
        </head>
        <body>
        """
        
        for index, card in enumerate(cards, 1):
            # 根据查询次数确定卡片样式
            if hasattr(card, 'view_count'):
                if card.view_count < 5:
                    card_class = "card-rare"
                elif 5 <= card.view_count < 10:
                    card_class = "card-common"
                else:
                    card_class = "card-frequent"
                view_count_text = f" | 查询次数: {card.view_count}"
            else:
                card_class = "card"
                view_count_text = ""
                
            html += f"""
            <div class="card {card_class}">
                <div class="card-info">卡片 #{index}{view_count_text}</div>
                <div class="module">{card.module}</div>
                <div class="content">{card.content}</div>
                {f'<div class="mnemonic">记忆口诀: {card.mnemonic}</div>' if card.mnemonic else ''}
            </div>
            """
        
        html += "</body></html>"
        return html
    
    def send_handler(send_type):
        dialog.close()
        try:
            # 获取卡片数据
            if send_type == "today":
                cards = window.db_manager.get_today_cards()
                subject = f"{datetime.datetime.now().strftime('%Y-%m-%d')} 知识卡片"
            elif send_type == "week":
                cards = window.db_manager.get_week_cards()
                today = datetime.datetime.now()
                week_start = today - datetime.timedelta(days=today.weekday())
                subject = f"{week_start.strftime('%Y-%m-%d')}至{today.strftime('%Y-%m-%d')} 知识卡片"
            elif send_type == "all":
                cards = window.db_manager.get_all_cards_sorted_by_views()
                subject = "全部知识卡片"
            else:
                cards = []
                subject = "知识卡片"
                
            if not cards:
                QMessageBox.information(window, "提示", "没有可发送的卡片")
                return
                
            # 转换为HTML
            html_content = convert_cards_to_html(cards)
            
            # 发送邮件
            result = send_email(html_content, subject)
            if result:
                QMessageBox.information(window, "发送成功", "卡片已成功发送")
            else:
                QMessageBox.warning(window, "发送失败", "卡片发送失败")
                
        except Exception as e:
            QMessageBox.critical(window, "错误", f"发送过程中出错: {str(e)}")
    
    # 连接按钮信号
    dialog.today_button.clicked.connect(lambda: send_handler("today"))
    dialog.week_button.clicked.connect(lambda: send_handler("week"))
    dialog.all_button.clicked.connect(lambda: send_handler("all"))
    dialog.select_button.clicked.connect(lambda: send_selected_date(window))
    
    dialog.exec()

def convert_cards_to_html(cards):
    """将卡片转换为HTML格式"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>知识卡片</title>
        <style>
            body { font-family: 'Microsoft YaHei', sans-serif; }
            .card { 
                border: 1px solid #0078d7;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
            }
            .module { 
                color: #0078d7;
                font-weight: bold;
                font-size: 16px;
            }
            .content { margin: 10px 0; }
            .mnemonic { 
                color: #ff0000;  /* 修改为红色 */
                font-style: italic;
            }
            .card-info {
                font-size: 12px;
                color: #888;
                margin-bottom: 5px;
            }
        </style>
    </head>
    <body>
    """
    
    for index, card in enumerate(cards, 1):
        created_time = datetime.datetime.strptime(card.created_at, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
        html += f"""
        <div class="card">
            <div class="card-info">卡片 #{index}</div>
            <div class="module">{card.module}</div>
            <div class="content">{card.content}</div>
            {f'<div class="mnemonic">记忆口诀: {card.mnemonic}</div>' if card.mnemonic else ''}
        </div>
        """
    
    html += "</body></html>"
    return html

def send_email(html_content, subject="知识卡片", silent=False):
    """发送邮件功能"""
    from utils.email_manager import EmailManager
    email_manager = EmailManager()
    config = email_manager.load_config()
    
    if not config:
        if not silent:
            QMessageBox.warning(None, "警告", "请先配置邮件设置")
        return False
        
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        msg = MIMEMultipart()
        msg['From'] = config['sender_email']
        msg['To'] = config['receiver_email']
        msg['Subject'] = subject
        
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP_SSL(config['smtp_server'], int(config['smtp_port'])) as server:
            server.login(config['sender_email'], config['auth_code'])
            try:
                server.send_message(msg)
                return True  # 直接返回True，不弹窗
            except smtplib.SMTPResponseException as e:
                # 特殊处理这个错误，直接返回True不弹窗
                if e.smtp_code == -1 and e.smtp_error == b'\x00\x00\x00':
                    return True
                return False
                
    except Exception as e:
        return False

def send_selected_date(window):
    """选择日期发送功能"""
    from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                                QPushButton, QListWidget, QCalendarWidget)
    from PyQt6.QtCore import QDate, Qt
    
    dialog = QDialog(window)
    dialog.setWindowTitle("选择发送日期")
    dialog.resize(400, 500)
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
    ok_btn = QPushButton("确定发送")
    
    # 布局
    layout.addWidget(calendar)
    layout.addLayout(btn_layout)
    layout.addWidget(date_list)
    layout.addWidget(ok_btn)
    
    def send_selected():
        selected_dates = [
            QDate.fromString(item.text(), "yyyy-MM-dd").toPyDate()
            for item in date_list.findItems("", Qt.MatchFlag.MatchContains)
        ]
        
        success_dates = []
        empty_dates = []
        
        for date in selected_dates:
            try:
                # 获取指定日期的卡片
                cards = window.db_manager.get_cards_by_date(date)
                if not cards:
                    empty_dates.append(date.strftime("%m月%d日"))
                    continue
                    
                # 转换为HTML并发送
                html_content = convert_cards_to_html(cards)
                subject = f"{date.strftime('%Y-%m-%d')} 知识卡片"  # 设置日期主题
                if send_email(html_content, subject):
                    success_dates.append(date.strftime("%m月%d日"))
                else:
                    empty_dates.append(date.strftime("%m月%d日"))
            except Exception as e:
                print(f"发送日期 {date} 失败: {e}")
                empty_dates.append(date.strftime("%m月%d日"))
        
        # 构建反馈消息
        message = ""
        if success_dates:
            message += f"成功发送以下日期的卡片:\n{', '.join(success_dates)}\n\n"
        if empty_dates:
            message += f"以下日期没有卡片或发送失败:\n{', '.join(empty_dates)}"
        
        if not success_dates and not empty_dates:
            message = "没有选择任何日期"
        elif not success_dates:
            message = f"您选择的日期({', '.join(empty_dates)})都没有卡片或发送失败"
        
        QMessageBox.information(window, "发送结果", message)
        dialog.accept()
    
    ok_btn.clicked.connect(send_selected)
    dialog.setLayout(layout)
    dialog.exec()

# 删除或注释掉这个方法，因为它会覆盖DBManager中的方法
# def get_cards_by_date(self, date):
#     """获取指定日期的卡片"""
#     start = datetime.datetime.combine(date, datetime.time.min)
#     end = datetime.datetime.combine(date, datetime.time.max)
#     return self.session.query(KnowledgeCard).filter(
#         KnowledgeCard.updated_at.between(start, end)
#     ).all()
def send_forget_cards(window):
    """发送易忘卡片功能"""
    try:
        # 获取所有卡片并按查询次数排序(从高到低)
        cards = window.db_manager.get_all_cards_sorted_by_views()
        if not cards:
            QMessageBox.information(window, "提示", "没有可发送的卡片")
            return
            
        # 按查询次数排序(从高到低)
        # cards.sort(key=lambda x: getattr(x, 'view_count', 0), reverse=True)
        cards.sort(key=lambda x: getattr(x, 'query_count', 0), reverse=True)  # 修改为query_count
        
        # 转换为HTML
        html_content = convert_forget_cards_to_html(cards)
        subject = "容易遗忘的卡片"
        
        # 发送邮件
        result = send_email(html_content, subject)
        if result:
            QMessageBox.information(window, "发送成功", "易忘卡片已成功发送")
        else:
            QMessageBox.warning(window, "发送失败", "易忘卡片发送失败")
            
    except Exception as e:
        QMessageBox.critical(window, "错误", f"发送过程中出错: {str(e)}")

def convert_forget_cards_to_html(cards):
    """将易忘卡片转换为HTML格式(特殊样式)"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>容易遗忘的卡片</title>
        <style>
            body {
                font-family: 'Microsoft YaHei', sans-serif;
                background-color: #f8f9fa;
                padding: 20px;
                color: #333;
            }
            .card-container {
                max-width: 800px;
                margin: 0 auto;
            }
            .card {
                border: 1px solid #ff6b6b;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 20px;
                background-color: white;
                box-shadow: 0 3px 10px rgba(255,107,107,0.1);
                cursor: pointer;
            }
            .card-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }
            .module {
                color: #ff6b6b;
                font-weight: bold;
                font-size: 18px;
                margin: 0;
            }
            .view-count {
                color: #ff6b6b;
                font-weight: bold;
                font-size: 14px;
                background-color: rgba(255,107,107,0.1);
                padding: 3px 8px;
                border-radius: 10px;
            }
            .content-preview {
                color: #555;
                font-size: 15px;
                margin: 10px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border-left: 3px solid #ff6b6b;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .content-full {
                display: none;
                color: #444;
                font-size: 15px;
                line-height: 1.6;
                margin: 15px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-radius: 5px;
                border-left: 3px solid #ff6b6b;
            }
            .mnemonic-container {
                display: none;
                margin-top: 15px;
                padding-top: 15px;
                border-top: 1px dashed #ddd;
            }
            .mnemonic-label {
                font-weight: bold;
                color: #ff6b6b;
                margin-bottom: 5px;
            }
            .mnemonic-content {
                color: #666;
                font-style: italic;
                font-size: 14px;
                line-height: 1.5;
            }
            .card-footer {
                margin-top: 10px;
                font-size: 12px;
                color: #999;
                text-align: right;
            }
            .expand-hint {
                color: #ff6b6b;
                font-size: 12px;
                text-align: right;
                margin-top: 5px;
                font-style: italic;
            }
            /* 使用:checked伪类实现无JS的展开效果 */
            .expand-toggle {
                display: none;
            }
            .expand-toggle:checked ~ .content-full,
            .expand-toggle:checked ~ .mnemonic-container {
                display: block;
            }
            .expand-toggle:checked ~ .expand-hint {
                display: none;
            }
        </style>
    </head>
    <body>
    <div class="card-container">
    <h1 style="color: #ff6b6b; text-align: center; margin-bottom: 30px;">容易遗忘的卡片</h1>
    <p style="text-align: center; color: #666; margin-bottom: 30px;">点击卡片查看完整内容</p>
    """

    for index, card in enumerate(cards, 1):
        # 获取内容的第一行
        first_line = (card.content.split('\n')[0] if card.content else "").strip()
        
        # 确保正确获取查询次数
        # view_count = card.query_count if hasattr(card, 'query_count') else 0
        view_count = getattr(card, 'query_count', 0)
        html += f"""
        <div class="card">
            <input type="checkbox" id="toggle-{index}" class="expand-toggle">
            <div class="card-header">
                <h2 class="module">{card.module}</h2>
                <div class="view-count">查询次数: {view_count}</div>
            </div>
            
            <label for="toggle-{index}">
                <div class="content-preview">{first_line}</div>
            </label>
            <div class="content-full">{card.content}</div>
            
            {f'''
            <div class="mnemonic-container">
                <div class="mnemonic-label">记忆口诀</div>
                <div class="mnemonic-content">{card.mnemonic}</div>
            </div>
            ''' if card.mnemonic else ''}
            
            <label for="toggle-{index}" class="expand-hint">点击展开完整内容</label>
            <div class="card-footer">卡片 #{index}</div>
        </div>
        """

    html += """
    </div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    main()

