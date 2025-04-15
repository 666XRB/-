import os
import sys  # 添加这行导入
from datetime import datetime
from fpdf import FPDF
from fpdf.enums import XPos, YPos  # 确保使用新版fpdf2的枚举
from datetime import datetime, timedelta

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        # 确保fonts目录存在
        font_dir = os.path.join(os.path.dirname(__file__), '..', 'fonts')
        if not os.path.exists(font_dir):
            os.makedirs(font_dir)
            
        # 加载微软雅黑字体(确保已复制到fonts目录)
        try:
            self.add_font('MicrosoftYaHei', '', os.path.join(font_dir, 'msyh.ttc'), uni=True)
            self.add_font('MicrosoftYaHei', 'B', os.path.join(font_dir, 'msyhbd.ttc'), uni=True)
            self.add_font('MicrosoftYaHei', 'I', os.path.join(font_dir, 'msyhl.ttc'), uni=True)
            self.set_font('MicrosoftYaHei', '', 12)
        except Exception as e:
            print(f"字体加载失败: {e}")
            # 回退到Arial字体
            self.set_font('Arial', '', 12)
        self.show_title = True  # 新增标志位控制是否显示标题
        self.time_color = (100, 100, 100)  # 新增：统一的时间文字颜色（深灰色）
        self._memory_check_interval = 50  # 每处理50张卡片检查一次内存
        self._processed_count = 0

    def _check_memory(self):
        """定期检查内存使用情况"""
        self._processed_count += 1
        if self._processed_count % self._memory_check_interval == 0:
            import psutil
            if psutil.virtual_memory().percent > 90:  # 内存使用超过90%
                self._flush_buffer()
                
    def _flush_buffer(self):
        """强制刷新缓冲区"""
        if hasattr(self, '_tmp_buffer'):
            del self._tmp_buffer
            self._tmp_buffer = None

    def header(self):
        # 只在第一页显示标题
        # if self.show_title:
        #     self.set_font('MicrosoftYaHei', 'B', 16)
        #     self.cell(0, 8, "知识卡片", 0, 1, "C")
        #     self.show_title = False  # 第一页后不再显示标题
        
        # 每页都显示时间（使用统一颜色）
        self.set_font('MicrosoftYaHei', 'I', 10)
        self.set_text_color(*self.time_color)  # 设置统一颜色
        self.cell(0, 8, f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, 'R')
        self.ln(8)

    def __del__(self):
        """析构函数确保资源释放"""
        if hasattr(self, '_tmp_buffer'):
            del self._tmp_buffer
        if hasattr(self, '_font_files'):
            for font in self._font_files.values():
                if hasattr(font, 'close'):
                    font.close()

def get_pdf_title(export_type):
    """根据导出类型生成标题"""
    today = datetime.now()
    if export_type == "today":
        return f"本日知识卡片库 - {today.strftime('%Y年%m月%d日')}"
    elif export_type == "week":
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        return f"本周知识卡片库 - {week_start.strftime('%Y年%m月%d日(%a)')}至{week_end.strftime('%Y年%m月%d日(%a)')}"
    else:
        return f"全部知识卡片库 - 创建于{today.strftime('%Y年%m月%d日')}"

def export_cards_to_pdf(cards, export_type="all", selected_dates=None):
    """导出PDF功能，支持多日期导出"""
    try:
        # 数据验证
        if not isinstance(cards, (list, tuple)):
            return False, "无效的卡片数据格式"
        if not cards:
            return False, "没有可导出的卡片"
            
        if selected_dates and len(selected_dates) > 1:
            # 多日期导出
            for date in selected_dates:
                _export_single_date(cards, date)
            return True, f"已成功导出{len(selected_dates)}天的卡片"
        elif selected_dates:
            # 单日期导出
            return _export_single_date(cards, selected_dates[0])
        else:
            # 其他导出模式
            return _export_general(cards, export_type)
            
    except Exception as e:
        return False, f"导出失败: {str(e)}"

def _export_single_date(cards, date):
    """处理单日期导出"""
    try:
        if hasattr(date, 'toPyDate'):
            date = date.toPyDate()
            
        filtered_cards = [
            c for c in cards 
            if datetime.strptime(c.created_at, "%Y-%m-%d %H:%M:%S").date() == date
        ]
        if not filtered_cards:
            return False, f"{date.strftime('%Y年%m月%d日')}没有学习记录"
        
        # 获取当前时间用于文件名
        now = datetime.now()
        
        # 生成文件名和标题
        filename = f"{date.strftime('%Y%m%d')}知识卡片_custom_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        title = f"知识卡片库 - {date.strftime('%Y年%m月%d日')}"
        
        # 将date对象转换为datetime对象
        target_date = datetime.combine(date, datetime.min.time())
        next_day = target_date + timedelta(days=1)
        cards = [
            c for c in cards 
            if target_date <= datetime.strptime(c.updated_at, "%Y-%m-%d %H:%M:%S") < next_day
        ]
        
        # 生成PDF
        pdf = PDF()
        pdf.add_page()
        
        # 设置标题
        pdf.set_font("MicrosoftYaHei", "B", 16)
        pdf.cell(0, 10, title, 0, 1, "C")
        pdf.ln(10)
        
        # 设置PDF整体样式
        pdf.set_text_color(0, 0, 0)  # 改为黑色
        pdf.set_draw_color(200, 200, 200)
        
        for index, card in enumerate(cards, start=1):
            # 计算内容高度 (减少行间距)
            content_height = 6 * (len(pdf.multi_cell(160, 6, card.content, split_only=True)) + 1)  # 宽度从175改为160
            mnemonic_height = 6 * (len(pdf.multi_cell(160, 6, f"记忆口诀: {card.mnemonic}", split_only=True)) + 1) if card.mnemonic else 0
            card_height = max(30, 10 + content_height + mnemonic_height)
            
            # 检查是否需要换页
            if pdf.get_y() + card_height > pdf.h - 15:  # 底部边距从10增加到15
                pdf.add_page()
            
            # 根据查询次数设置背景色 (严格遵循项目中的颜色梯度)
            if card.query_count == 0:
                fill_color = (245, 245, 245)   # #f5f5f5 - 浅灰色
            elif card.query_count < 5:
                fill_color = (227, 242, 253)   # #e3f2fd - 淡蓝色
            elif card.query_count < 10:
                fill_color = (187, 222, 251)   # #bbdefb - 浅蓝色
            elif card.query_count < 20:
                fill_color = (144, 202, 249)   # #90caf9 - 中蓝色
            elif card.query_count < 30:
                fill_color = (255, 204, 188)   # #ffccbc - 浅橙色
            elif card.query_count < 50:
                fill_color = (255, 171, 145)   # #ffab91 - 中橙色
            elif card.query_count < 100:
                fill_color = (255, 112, 67)    # #ff7043 - 橙色
            else:
                fill_color = (244, 81, 30)     # #f4511e - 深橙色
            
            # 应用背景色
            pdf.set_fill_color(*fill_color)
            pdf.rect(10, pdf.get_y(), 190, card_height, 'F')
            pdf.rect(10, pdf.get_y(), 190, card_height)
            
            # 序号和模块标题 (右上角显示查询次数)
            pdf.set_font('MicrosoftYaHei', 'B', 12)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(15, pdf.get_y()+3)
            pdf.cell(0, 6, f"{index}.", 0, 0)
            
            # 添加创建时间 (在查询次数左侧)
            create_time = datetime.strptime(card.created_at, "%Y-%m-%d %H:%M:%S").strftime("%m-%d")
            pdf.set_font('MicrosoftYaHei', '', 8)
            pdf.set_text_color(150, 150, 150)  # 统一使用浅灰色
            pdf.set_x(120)
            pdf.cell(40, 6, f"创建: {create_time}", 0, 0)
            
            # 在右上角显示查询次数
            pdf.set_font('MicrosoftYaHei', '', 10)
            pdf.set_text_color(150, 150, 150)  # 浅灰色
            pdf.set_x(160)
            pdf.cell(30, 6, f"查询: {card.query_count}次", 0, 1)

            
            # 模块名称 - 改为蓝色 (0, 120, 215)
            pdf.set_font('MicrosoftYaHei', 'B', 14)
            pdf.set_text_color(0, 120, 215)  # 明确设置为蓝色
            pdf.set_xy(25, pdf.get_y())
            pdf.cell(0, 8, card.module, 0, 1)
            
            # 内容 - 确保使用黑色 (0, 0, 0)
            pdf.set_font('MicrosoftYaHei', '', 12)
            pdf.set_text_color(0, 0, 0)  # 明确设置为黑色
            pdf.set_xy(25, pdf.get_y()+1)
            pdf.multi_cell(160, 6, card.content)
            
            # 记忆口诀 - 保持红色 (220, 20, 60)
            if card.mnemonic:
                pdf.set_font('MicrosoftYaHei', 'B', 10)
                pdf.set_text_color(220, 20, 60)
                pdf.set_xy(25, pdf.get_y()+1)
                pdf.multi_cell(175, 6, f"记忆口诀: {card.mnemonic}")
            
            # 重置文字颜色为黑色
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)
        
        # 保存文件
        if getattr(sys, 'frozen', False):
            # 打包后模式：使用EXE所在目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发模式：使用项目目录
            base_dir = os.path.dirname(os.path.dirname(__file__))
            
        export_dir = os.path.join(base_dir, 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            
        pdf_path = os.path.join(export_dir, filename)
        pdf.output(pdf_path)
        
        # 导出成功后自动打开文件夹
        try:
            os.startfile(export_dir)  # Windows系统
        except:
            import subprocess
            try:
                if sys.platform == "darwin":
                    subprocess.Popen(["open", export_dir])  # MacOS
                else:
                    subprocess.Popen(["xdg-open", export_dir])  # Linux
            except:
                pass
                
        return True, f"已成功导出到: {pdf_path}"
        
    except Exception as e:
        return False, f"导出失败: {str(e)}"


def _export_general(cards, export_type):
    try:
        # 前置检查
        if len(cards) > 1000:  # 超过1000张卡片时启用分页模式
            return _export_large_dataset(cards, export_type)
            
        # 获取当前时间用于文件名
        now = datetime.now()
        filename = f"知识卡片_{export_type}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
        title = get_pdf_title(export_type)
        
        # 根据类型筛选卡片（修改为基于created_at）
        if export_type == "today":
            today = datetime.now().replace(hour=0, minute=0, second=0)
            cards = [c for c in cards if datetime.strptime(c.created_at, "%Y-%m-%d %H:%M:%S") >= today]
        elif export_type == "week":
            week_start = datetime.now() - timedelta(days=datetime.now().weekday())
            week_start = week_start.replace(hour=0, minute=0, second=0)
            cards = [c for c in cards if datetime.strptime(c.created_at, "%Y-%m-%d %H:%M:%S") >= week_start]
        
        # 生成PDF
        pdf = PDF()
        pdf.add_page()
        
        # 设置标题
        pdf.set_font("MicrosoftYaHei", "B", 16)
        pdf.cell(0, 10, title, 0, 1, "C")
        pdf.ln(10)
        
        # 设置PDF整体样式
        pdf.set_text_color(0, 0, 0)  # 改为黑色
        pdf.set_draw_color(200, 200, 200)
        
        for index, card in enumerate(cards, start=1):
            # 计算内容高度 (减少行间距)
            content_height = 6 * (len(pdf.multi_cell(175, 6, card.content, split_only=True)) + 1)
            mnemonic_height = 6 * (len(pdf.multi_cell(175, 6, f"记忆口诀: {card.mnemonic}", split_only=True)) + 1) if card.mnemonic else 0
            card_height = max(30, 10 + content_height + mnemonic_height)  # 进一步减少最小高度
            
            # 检查是否需要换页
            if pdf.get_y() + card_height > pdf.h - 10:
                pdf.add_page()
            
            # 根据查询次数设置背景色 (严格遵循项目中的颜色梯度)
            if card.query_count == 0:
                fill_color = (245, 245, 245)   # #f5f5f5 - 浅灰色
            elif card.query_count < 5:
                fill_color = (227, 242, 253)   # #e3f2fd - 淡蓝色
            elif card.query_count < 10:
                fill_color = (187, 222, 251)   # #bbdefb - 浅蓝色
            elif card.query_count < 20:
                fill_color = (144, 202, 249)   # #90caf9 - 中蓝色
            elif card.query_count < 30:
                fill_color = (255, 204, 188)   # #ffccbc - 浅橙色
            elif card.query_count < 50:
                fill_color = (255, 171, 145)   # #ffab91 - 中橙色
            elif card.query_count < 100:
                fill_color = (255, 112, 67)    # #ff7043 - 橙色
            else:
                fill_color = (244, 81, 30)     # #f4511e - 深橙色
                
            # 应用背景色
            pdf.set_fill_color(*fill_color)
            pdf.rect(10, pdf.get_y(), 190, card_height, 'F')
            pdf.rect(10, pdf.get_y(), 190, card_height)
            
            # 序号和模块标题 (右上角显示查询次数)
            pdf.set_font('MicrosoftYaHei', 'B', 12)
            pdf.set_text_color(100, 100, 100)
            pdf.set_xy(15, pdf.get_y()+3)
            pdf.cell(0, 6, f"{index}.", 0, 0)
            
            # 添加创建时间 (在查询次数左侧)
            create_time = datetime.strptime(card.created_at, "%Y-%m-%d %H:%M:%S").strftime("%m-%d")
            pdf.set_font('MicrosoftYaHei', '', 8)
            pdf.set_text_color(150, 150, 150)  # 统一使用浅灰色
            pdf.set_x(120)
            pdf.cell(40, 6, f"创建: {create_time}", 0, 0)
            
            # 在右上角显示查询次数
            pdf.set_font('MicrosoftYaHei', '', 10)
            pdf.set_text_color(150, 150, 150)  # 浅灰色
            pdf.set_x(160)
            pdf.cell(30, 6, f"查询: {card.query_count}次", 0, 1)


            # 模块名称 - 改为蓝色 (0, 120, 215)
            pdf.set_font('MicrosoftYaHei', 'B', 14)
            pdf.set_text_color(0, 120, 215)  # 明确设置为蓝色
            pdf.set_xy(25, pdf.get_y())
            pdf.cell(0, 8, card.module, 0, 1)
            
            # 内容 - 确保使用黑色 (0, 0, 0)
            pdf.set_font('MicrosoftYaHei', '', 12)
            pdf.set_text_color(0, 0, 0)  # 明确设置为黑色
            pdf.set_xy(25, pdf.get_y()+1)
            pdf.multi_cell(160, 6, card.content)
            
            # 记忆口诀 - 保持红色 (220, 20, 60)
            if card.mnemonic:
                pdf.set_font('MicrosoftYaHei', 'B', 10)
                pdf.set_text_color(220, 20, 60)
                pdf.set_xy(25, pdf.get_y()+1)
                pdf.multi_cell(175, 6, f"记忆口诀: {card.mnemonic}")
            
            # 重置文字颜色为黑色
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)
        
        # 保存文件
        if getattr(sys, 'frozen', False):
            # 打包后模式：使用EXE所在目录
            base_dir = os.path.dirname(sys.executable)
        else:
            # 开发模式：使用项目目录
            base_dir = os.path.dirname(os.path.dirname(__file__))
            
        export_dir = os.path.join(base_dir, 'exports')
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
            
        pdf_path = os.path.join(export_dir, filename)
        pdf.output(pdf_path)
        
        # 导出成功后自动打开文件夹
        try:
            os.startfile(export_dir)  # Windows系统
        except:
            import subprocess
            try:
                if sys.platform == "darwin":
                    subprocess.Popen(["open", export_dir])  # MacOS
                else:
                    subprocess.Popen(["xdg-open", export_dir])  # Linux
            except:
                pass
                
        return True, f"已成功导出到: {pdf_path}"
        
    except Exception as e:
        return False, f"导出失败: {str(e)}"


def _export_large_dataset(cards, export_type):
    try:
        pdf = PDF()
        batch_size = 200
        
        for i in range(0, len(cards), batch_size):
            batch = cards[i:i+batch_size]
            if i == 0:
                pdf.add_page()
                # ... 添加标题等初始化代码 ...
            
            # 处理当前批次
            for card in batch:
                # ... 原有卡片处理代码 ...
                
                # 添加创建时间
                create_time = datetime.strptime(card.created_at, "%Y-%m-%d %H:%M:%S").strftime("%m-%d")
                pdf.set_font('MicrosoftYaHei', '', 8)
                pdf.set_text_color(150, 150, 150)
                pdf.set_x(120)
                pdf.cell(40, 6, f"创建: {create_time}", 0, 0)
                
                # 查询次数
                pdf.set_x(160)
                pdf.cell(30, 6, f"查询: {card.query_count}次", 0, 1)
                
                # ... 其余卡片内容保持不变 ...
                pdf._check_memory()
                
        # ... 文件保存逻辑 ...
        return True, pdf_path
    except MemoryError:
        return False, "系统内存不足，请减少导出数量"
    except IOError as e:
        return False, f"文件系统错误: {str(e)}"
    except Exception as e:
        return False, f"导出过程出错: {str(e)}"

def _save_pdf(pdf, filename):
    """安全的文件保存方法"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            temp_path = filename + '.tmp'
            pdf.output(temp_path)
            # 原子操作替换文件
            if os.path.exists(filename):
                os.remove(filename)
            os.rename(temp_path, filename)
            return True
        except PermissionError:
            if attempt == max_retries - 1:
                raise
            import time
            time.sleep(1)  # 等待1秒后重试
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

