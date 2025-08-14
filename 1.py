import sys
import os
import shutil
import json
from pathlib import Path

# -------------------------------------------------------------------
# 辅助函数保持不变
# -------------------------------------------------------------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def setup_external_fonts():
    try:
        if getattr(sys, 'frozen', False):
            application_path = Path(os.path.dirname(sys.executable))
        else:
            application_path = Path(os.path.dirname(os.path.abspath(__file__)))
        external_fonts_dir = application_path / "fonts"
        if not external_fonts_dir.exists():
            external_fonts_dir.mkdir(parents=True, exist_ok=True)
            internal_default_fonts_dir = Path(resource_path("default_fonts"))
            if internal_default_fonts_dir.is_dir():
                for font_file in internal_default_fonts_dir.iterdir():
                    if font_file.is_file() and font_file.name.lower().endswith(('.ttf', '.otf', '.ttc')):
                        shutil.copy(font_file, external_fonts_dir / font_file.name)
    except Exception as e:
        print(f"错误：创建或复制默认字体时失败: {e}")

def setup_fcitx5_im_plugin():
    if sys.platform != "linux": return
    try:
        import PyQt5
        pyqt_path = Path(PyQt5.__file__).parent
        target_plugin_dir = pyqt_path / "Qt5" / "plugins" / "platforminputcontexts"
        target_plugin_file = target_plugin_dir / "libfcitx5platforminputcontextplugin.so"
        source_plugin_file = Path(resource_path("lib/libfcitx5platforminputcontextplugin.so"))
        if not source_plugin_file.exists(): return
        if target_plugin_file.exists(): return
        target_plugin_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(source_plugin_file, target_plugin_dir)
    except Exception as e:
        print(f"自动注入 Fcitx5 插件时发生错误: {e}")

# -------------------------------------------------------------------
# 导入qt模块（好多）
# -------------------------------------------------------------------
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QLabel, QFileDialog, QMessageBox, QFrame,
    QListWidget, QListWidgetItem, QSplitter, QSlider, QGraphicsDropShadowEffect,
    QStyledItemDelegate, QStyle, QStyleOptionViewItem, QMenu
)
from PyQt5.QtGui import QFont, QFontDatabase, QPainter, QPixmap, QColor, QTextDocument, QIcon, QFontInfo
from PyQt5.QtCore import Qt, pyqtSignal

# -------------------------------------------------------------------
# CustomItemDelegate
# -------------------------------------------------------------------
class CustomItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.font = QFont("sans-serif", 12)
    def paint(self, painter, option, index):
        opt = QStyleOptionViewItem(option); self.initStyleOption(opt, index); painter.save(); rect = opt.rect; text = opt.text
        is_selected = opt.state & QStyle.State_Selected; is_active = opt.state & QStyle.State_Active
        bg_color = QColor("#4A90E2") if (is_selected and is_active) else Qt.transparent
        text_color = Qt.white if (is_selected and is_active) else QColor("#1A2530") if is_selected else QColor("#333333")
        bg_rect = rect.adjusted(9, 4, -5, -4); text_rect = bg_rect.adjusted(6, 0, -6, 0)
        painter.setBrush(bg_color); painter.setPen(Qt.NoPen); painter.drawRoundedRect(bg_rect, 8, 8)
        painter.setFont(self.font); painter.setPen(text_color); painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, text)
        painter.restore()
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index); size.setHeight(36); return size

# -------------------------------------------------------------------
# 自定义字体列表控件，以支持拖放安装
# -------------------------------------------------------------------
class FontListWidget(QListWidget):
    # 定义一个信号，当字体被成功拖放并复制后，发射这个信号
    fontDropped = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.fonts_dir = self.get_app_path() / "fonts"

    def get_app_path(self):
        if getattr(sys, 'frozen', False):
            return Path(os.path.dirname(sys.executable))
        return Path(os.path.dirname(os.path.abspath(__file__)))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith(('.ttf', '.otf', '.ttc')) for url in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            source_path = Path(url.toLocalFile())
            
            if not source_path.name.lower().endswith(('.ttf', '.otf', '.ttc')):
                continue

            target_path = self.fonts_dir / source_path.name

            if target_path.exists():
                print(f"字体 '{source_path.name}' 已存在，跳过。")
                continue

            try:
                shutil.copy(source_path, target_path)
                # 发射信号，并传递新复制的字体文件的路径
                self.fontDropped.emit(str(target_path))
            except Exception as e:
                print(f"复制字体 '{source_path.name}' 时失败: {e}")
                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setText(f"无法安装字体 '{source_path.name}'。")
                msg_box.setInformativeText(str(e))
                msg_box.exec_()

# -------------------------------------------------------------------
# QSS
# -------------------------------------------------------------------
CUSTOM_STYLESHEET_TEMPLATE = """
    QMainWindow, QWidget#CentralWidget {{
        background-color: #F0F4F8;
        font-family: sans-serif;
    }}
    QWidget#ShadowContainer {{
        background-color: transparent;
    }}
    QFrame#SidebarFrame, QFrame#RightSidebar {{
        background-color: #FFFFFF;
        border-radius: 8px;
        border: 1px solid #E1E8ED;
    }}
    QPushButton {{
        background-color: #FFFFFF;
        color: #333;
        border: 1px solid #DDE4E8;
        padding: 10px 15px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
    }}
    QPushButton:hover {{ background-color: #F5F8FA; }}
    QPushButton:pressed {{ background-color: #E1E8ED; }}
    QLineEdit {{
        background-color: #FFFFFF;
        border: 1px solid #DDE4E8;
        border-radius: 8px;
        padding: 10px;
        font-size: 16px;
        color: #222;
    }}
    QLineEdit:focus {{ border: 2px solid #4A90E2; }}
    QListWidget {{
        border: none;
        background-color: transparent;
        outline: none;
    }}
    QListWidget QScrollBar:vertical {{
        width: 8px;
        background: transparent;
    }}
    QListWidget QScrollBar::handle:vertical {{
        background: #c0c0c0;
        min-height: 20px;
        border-radius: 4px;
    }}
    QSlider::groove:horizontal {{
        border: 1px solid #DDE4E8;
        height: 4px;
        background: #E8EDF2;
        margin: 0;
        border-radius: 2px;
    }}
    QSlider::handle:horizontal {{
        image: url({handle_image_path});
        border: none;
        width: 15px;
        height: 15px;
        margin-top: -10px;
        margin-bottom: -10px;
    }}
    QSlider::handle:horizontal:pressed {{
        image: url({handle_pressed_image_path});
    }}
    QLabel {{ color: #3D4F61; font-size: 14px; }}
    QLabel#TitleLabel {{ font-weight: bold; font-size: 18px; color: #1A2530; padding-bottom: 5px; }}
    QLabel#ValueLabel {{ font-weight: bold; font-size: 16px; color: #4A90E2; }}
    QSplitter::handle {{ background-color: #D0D8E0; }}
    QSplitter::handle:horizontal {{ width: 4px; }}
    QSplitter::handle:hover {{ background-color: #FFFFFF; }}
"""
FILE_DIALOG_STYLESHEET = """
    QFileDialog {
        background-color: #F0F4F8;
        font-family: sans-serif;
    }
    QFileDialog QLabel {
        color: #3D4F61;
        font-size: 14px;
    }
    /* "打开" 和 "取消" 按钮 */
    QFileDialog QPushButton {
        background-color: #4A90E2;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
    }
    QFileDialog QPushButton:hover {
        background-color: #5B9BD5;
    }
    QFileDialog QPushButton:pressed {
        background-color: #4472C4;
    }
    /* 对“取消”按钮或其他非默认按钮做区分 */
    QFileDialog QPushButton[text='Cancel'],
    QFileDialog QPushButton[text='取消'] {
        background-color: #E1E8ED;
        color: #3D4F61;
    }
    QFileDialog QPushButton[text='Cancel']:hover,
    QFileDialog QPushButton[text='取消']:hover {
        background-color: #D0D8E0;
    }
"""
# -------------------------------------------------------------------
# 主窗口
# -------------------------------------------------------------------
INITIAL_FONT_SIZE = 32
MIN_FONT_SIZE = 8
MAX_FONT_SIZE = 300
class FontViewerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        setup_external_fonts()
        self.config_path = self.get_config_path()
        self.saved_font_paths = self.load_saved_paths()
        self.setup_stylesheet()
        self.current_font_id = -1
        self.current_font_family = ""
        self.preview_font_size = INITIAL_FONT_SIZE
        self.init_ui()
        self.load_initial_fonts()

    def get_app_path(self):
        if getattr(sys, 'frozen', False): return Path(os.path.dirname(sys.executable))
        return Path(os.path.dirname(os.path.abspath(__file__)))

    def get_config_path(self):
        return self.get_app_path() / "fonts" / "saved_paths.json"

    def load_saved_paths(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    paths = json.load(f)
                    return [p for p in paths if Path(p).exists()]
            except (json.JSONDecodeError, IOError): return []
        return []

    def save_paths(self):
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.saved_font_paths, f, indent=4)
        except IOError as e: print(f"保存路径失败: {e}")

    def setup_stylesheet(self):
        handle_path = resource_path("assets/radio-checked-hover@2x.png")
        handle_pressed_path = resource_path("assets/radio-checked-hover-press@2x.png")
        handle_path_str = str(Path(handle_path).as_posix())
        handle_pressed_path_str = str(Path(handle_pressed_path).as_posix())
        self.final_stylesheet = CUSTOM_STYLESHEET_TEMPLATE.format(
            handle_image_path=f"'{handle_path_str}'",
            handle_pressed_image_path=f"'{handle_pressed_path_str}'"
        )

    def init_ui(self):
        self.setWindowTitle("字体预览器"); self.setGeometry(100, 100, 1200, 700); self.setMinimumSize(900, 600)
        central_widget = QWidget(); central_widget.setObjectName("CentralWidget"); self.setCentralWidget(central_widget); self.setStyleSheet(self.final_stylesheet)
        main_splitter = QSplitter(Qt.Horizontal)
        left_shadow_container = QWidget(); left_shadow_container.setObjectName("ShadowContainer"); shadow_layout = QVBoxLayout(left_shadow_container); shadow_layout.setContentsMargins(10, 10, 10, 10)
        left_sidebar = QFrame(); left_sidebar.setObjectName("SidebarFrame"); shadow_layout.addWidget(left_sidebar)
        shadow_left = QGraphicsDropShadowEffect(self); shadow_left.setBlurRadius(25); shadow_left.setXOffset(0); shadow_left.setYOffset(4); shadow_left.setColor(QColor(0, 0, 0, 30)); left_shadow_container.setGraphicsEffect(shadow_left)
        sidebar_layout = QVBoxLayout(left_sidebar); sidebar_layout.setContentsMargins(10, 10, 10, 10); sidebar_layout.setSpacing(10)
        sidebar_title = QLabel("字体选择"); sidebar_title.setObjectName("TitleLabel")
        
        # 使用FontListWidget
        self.font_list_widget = FontListWidget(self)
        self.font_list_widget.setItemDelegate(CustomItemDelegate(self.font_list_widget))
        self.font_list_widget.itemClicked.connect(self.on_font_selected)
        self.font_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.font_list_widget.customContextMenuRequested.connect(self.show_font_context_menu)
        # 连接自定义的 fontDropped 信号到 add_font_to_list 槽函数
        self.font_list_widget.fontDropped.connect(self.add_font_to_list)

        add_font_button = QPushButton("添加字体..."); add_font_button.clicked.connect(self.add_font_file)
        sidebar_layout.addWidget(sidebar_title); sidebar_layout.addWidget(self.font_list_widget); sidebar_layout.addWidget(add_font_button)
        
        # 中央和右侧UI代码
        center_frame = QFrame(); center_layout = QVBoxLayout(center_frame); center_layout.setContentsMargins(10, 10, 10, 10); center_layout.setSpacing(20)
        self.text_entry = QLineEdit(); self.text_entry.setPlaceholderText("在这里打字，看看字体的样子... 😄"); self.text_entry.textChanged.connect(self.update_preview)
        self.preview_label = QLabel("\n从左边选一个字体开始查看吧！"); self.preview_label.setAlignment(Qt.AlignCenter); self.preview_label.setStyleSheet("background-color: #FFFFFF; border-radius: 12px;"); self.preview_label.setMinimumHeight(300)
        size_control_frame = QFrame(); size_control_layout = QHBoxLayout(size_control_frame); size_control_layout.setContentsMargins(0, 0, 0, 0)
        size_label = QLabel("字体大小:"); self.size_slider = QSlider(Qt.Horizontal); self.size_slider.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE); self.size_slider.setValue(INITIAL_FONT_SIZE); self.size_slider.valueChanged.connect(self.on_size_changed)
        self.size_value_label = QLabel(str(INITIAL_FONT_SIZE)); self.size_value_label.setObjectName("ValueLabel"); self.size_value_label.setMinimumWidth(40)
        size_control_layout.addWidget(size_label); size_control_layout.addWidget(self.size_slider); size_control_layout.addWidget(self.size_value_label)
        center_layout.addWidget(self.text_entry); center_layout.addWidget(self.preview_label, 1); center_layout.addWidget(size_control_frame)
        right_shadow_container = QWidget()
        right_shadow_container.setObjectName("ShadowContainer")
        right_shadow_container.setFixedWidth(240)
        right_shadow_layout = QVBoxLayout(right_shadow_container)
        right_shadow_layout.setContentsMargins(10, 10, 10, 10)
        right_sidebar = QFrame()
        right_sidebar.setObjectName("RightSidebar")
        right_shadow_layout.addWidget(right_sidebar)
        shadow_right = QGraphicsDropShadowEffect(self)
        shadow_right.setBlurRadius(25)
        shadow_right.setXOffset(0)
        shadow_right.setYOffset(4)
        shadow_right.setColor(QColor(0, 0, 0, 30))
        right_shadow_container.setGraphicsEffect(shadow_right)
        info_layout = QVBoxLayout(right_sidebar)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        info_title = QLabel("字体信息")
        info_title.setObjectName("TitleLabel")
        self.font_name_label = QLabel("待选择")
        self.font_path_label = QLabel("待选择")
        self.font_size_label = QLabel("待选择")
        self.font_style_label = QLabel("待选择")
        self.font_weight_label = QLabel("待选择")
        self.font_italic_label = QLabel("待选择")
        for lb in (self.font_name_label, self.font_path_label, self.font_size_label, 
                   self.font_style_label, self.font_weight_label, self.font_italic_label):
            lb.setWordWrap(True)
            lb.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        info_layout.addWidget(info_title)
        info_layout.addWidget(QLabel("家族 (Family):"))
        info_layout.addWidget(self.font_name_label)
        info_layout.addWidget(QLabel("风格 (Style):"))
        info_layout.addWidget(self.font_style_label)
        info_layout.addWidget(QLabel("粗细 (Weight):"))
        info_layout.addWidget(self.font_weight_label)
        info_layout.addWidget(QLabel("斜体 (Italic):"))
        info_layout.addWidget(self.font_italic_label)
        info_layout.addWidget(QLabel("文件路径:"))
        info_layout.addWidget(self.font_path_label)
        info_layout.addWidget(QLabel("文件大小:"))
        info_layout.addWidget(self.font_size_label)
        info_layout.addStretch(1)
        info_button = QPushButton("关于")
        info_button.clicked.connect(self.show_info_dialog)
        info_layout.addWidget(info_button)
        main_splitter.addWidget(left_shadow_container); main_splitter.addWidget(center_frame); main_splitter.addWidget(right_shadow_container); main_splitter.setSizes([280, 700, 240])
        final_layout = QHBoxLayout(central_widget); final_layout.setContentsMargins(0, 0, 0, 0); final_layout.setSpacing(0); final_layout.addWidget(main_splitter)

    def load_initial_fonts(self):
        app_path = self.get_app_path(); fonts_dir = app_path / "fonts"

        if fonts_dir.is_dir():
            font_files = sorted(fonts_dir.glob("*.ttf")) + sorted(fonts_dir.glob("*.otf"))
            for font_path in font_files: self.add_font_to_list(str(font_path))

        for path in self.saved_font_paths:
            self.add_font_to_list(path)

    def add_font_file(self):
        start_dir = str(self.get_app_path())
        
        dialog = QFileDialog(self, "选择字体文件", start_dir)
        
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        
        dialog.setNameFilter("字体文件 (*.ttf *.otf *.ttc);;所有文件 (*.*)")

        dialog.setFileMode(QFileDialog.ExistingFiles)

        dialog.setStyleSheet(FILE_DIALOG_STYLESHEET)
        
        filepaths = []

        if dialog.exec_():
            filepaths = dialog.selectedFiles()

        if not filepaths:
            return
        
        app_fonts_dir = self.get_app_path() / "fonts"
        for filepath in filepaths:
            path_obj = Path(filepath)
            
            if path_obj.parent == app_fonts_dir:
                self.add_font_to_list(filepath)
                continue
            
            if filepath not in self.saved_font_paths:
                self.saved_font_paths.append(filepath)
                self.add_font_to_list(filepath)
        
        self.save_paths()

    # 增加防重复检查
    def add_font_to_list(self, filepath):
        # 检查该路径是否已在列表中
        for i in range(self.font_list_widget.count()):
            if self.font_list_widget.item(i).data(Qt.UserRole) == filepath:
                print(f"字体路径 '{filepath}' 已在列表中，跳过添加。")
                return
        
        item = QListWidgetItem(os.path.basename(filepath))
        item.setData(Qt.UserRole, filepath)
        self.font_list_widget.addItem(item)

    def show_font_context_menu(self, pos):
        item = self.font_list_widget.itemAt(pos)
        if not item: return
        font_path = Path(item.data(Qt.UserRole)); app_fonts_dir = self.get_app_path() / "fonts"; is_internal = font_path.parent == app_fonts_dir
        menu = QMenu(); menu.setAttribute(Qt.WA_TranslucentBackground)
        delete_text = "删除字体文件" if is_internal else "删除快捷方式"; delete_action = menu.addAction(delete_text)
        menu.setStyleSheet("""
            QMenu { background-color: #FFFFFF; border: 3px solid #E1E8ED; border-radius: 8px; padding: 0px; font-family: sans-serif; }
            QMenu::item { padding: 8px 20px; border-radius: 6px; background-color: transparent; border: none; }
            QMenu::item:selected { background-color: #F0F4F8; }
            QMenu::item:pressed { background-color: #E1E8ED; }
        """)
        action = menu.exec_(self.font_list_widget.mapToGlobal(pos))
        if action == delete_action: self.delete_font_item(item, is_internal)
    def delete_font_item(self, item, is_internal):
        font_path_str = item.data(Qt.UserRole); font_path = Path(font_path_str)
        if is_internal:
            msg_box = QMessageBox(); msg_box.setWindowTitle('确认删除'); msg_box.setText("确定要从硬盘上永久删除字体文件吗？"); msg_box.setInformativeText(f"<b>{font_path.name}</b>"); msg_box.setIcon(QMessageBox.Warning)
            yes_button = msg_box.addButton("确认删除", QMessageBox.YesRole); no_button = msg_box.addButton("取消", QMessageBox.NoRole); msg_box.setDefaultButton(no_button)
            msg_box.setStyleSheet("""
                QMessageBox { background-color: #FFFFFF; border-radius: 12px; font-family: sans-serif; }
                QMessageBox QLabel#qt_msgbox_label { color: #1A2530; font-size: 16px; font-weight: bold; }
                QMessageBox QLabel#qt_msgbox_informabel { color: #586A7A; font-size: 14px; }
                QPushButton { border: none; padding: 8px 20px; border-radius: 6px; font-weight: bold; font-size: 14px; min-width: 80px; }
                QPushButton:hover { opacity: 0.9; }
                QPushButton[text='确认删除'] { background-color: #E53935; color: white; }
                QPushButton[text='确认删除']:hover { background-color: #D32F2F; }
                QPushButton[text='取消'] { background-color: #E1E8ED; color: #3D4F61; }
                QPushButton[text='取消']:hover { background-color: #D0D8E0; }
            """)
            msg_box.exec_()
            if msg_box.clickedButton() == yes_button:
                try:
                    os.remove(font_path); row = self.font_list_widget.row(item); self.font_list_widget.takeItem(row)
                except OSError as e: self.show_native_error_message("删除失败", f"无法删除文件: {e}")
        else:
            if font_path_str in self.saved_font_paths: self.saved_font_paths.remove(font_path_str); self.save_paths()
            row = self.font_list_widget.row(item); self.font_list_widget.takeItem(row)
    def on_font_selected(self, item):
        if not item: return
        filepath = item.data(Qt.UserRole)
        font_details = self.load_font(filepath)
        if font_details:
            family, style, weight, italic, font_id = font_details
            self.current_font_family = family; self.current_font_id = font_id
            self.font_name_label.setText(family); self.font_style_label.setText(style); self.font_weight_label.setText(f"{weight}"); self.font_italic_label.setText("是" if italic else "否"); self.font_path_label.setText(filepath)
            try: size_kb = Path(filepath).stat().st_size / 1024; self.font_size_label.setText(f"{size_kb:.1f} KB")
            except FileNotFoundError: self.font_size_label.setText("未知大小")
            self.update_preview()
    def load_font(self, filepath):
        if self.current_font_id != -1: QFontDatabase.removeApplicationFont(self.current_font_id)
        font_id = QFontDatabase.addApplicationFont(filepath)
        if font_id == -1: self.show_native_error_message("加载失败", f"无法加载字体文件:\n{filepath}"); return None
        families = QFontDatabase.applicationFontFamilies(font_id)
        if not families: self.show_native_error_message("加载失败", f"无法从此文件获取字体家族名称:\n{filepath}"); QFontDatabase.removeApplicationFont(font_id); return None
        family = families[0]
        db = QFontDatabase()
        available_styles = db.styles(family)
        style = available_styles[0] if available_styles else "Normal"
        exact_font = db.font(family, style, 12)
        font_info = QFontInfo(exact_font)
        weight = font_info.weight(); italic = font_info.italic()
        return family, style, weight, italic, font_id
    def on_size_changed(self, value):
        self.preview_font_size = value; self.size_value_label.setText(str(value)); self.update_preview()
    def update_preview(self):
        if not self.current_font_family: return
        text = self.text_entry.text(); font = QFont(self.current_font_family, self.preview_font_size); font.setStyleStrategy(QFont.PreferAntialias)
        rect = self.preview_label.rect(); pixmap = QPixmap(rect.size() * self.devicePixelRatioF()); pixmap.setDevicePixelRatio(self.devicePixelRatioF()); pixmap.fill(Qt.transparent)
        p = QPainter(pixmap); p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform); p.setFont(font); p.setPen(QColor("#222"))
        doc = QTextDocument(); doc.setDefaultFont(font); doc.setPlainText(text if text else "从左边选一个字体开始查看吧！"); doc.setTextWidth(rect.width() - 20)
        y = max((rect.height() - doc.size().height()) / 2, 0); p.translate(10, y); doc.drawContents(p); p.end()
        self.preview_label.setPixmap(pixmap)
    def show_native_error_message(self, title, text):
        msg_box = QMessageBox(); msg_box.setIcon(QMessageBox.Critical); msg_box.setWindowTitle("错误"); msg_box.setText(title); msg_box.setInformativeText(text); msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowStaysOnTopHint); msg_box.exec_()
    def show_info_dialog(self):
        msg = QMessageBox(); msg.setWindowTitle("字体预览器-关于"); msg.setText("版本：v2.0\n作者：天影大侠\n简介：使用PyQt5制作的本地字体实时预览工具，原是为了快速预览emoji，所以用python制作了这个小工具，接着就优化了一下成为了这个样子。")
        msg.setIcon(QMessageBox.NoIcon); msg.setStandardButtons(QMessageBox.Ok); msg.setDefaultButton(QMessageBox.Ok)
        ok_btn = msg.button(QMessageBox.Ok); ok_btn.setIcon(QIcon())
        msg.setStyleSheet("""
            QMessageBox { background-color:#FFFFFF; border-radius:12px; font-family:sans-serif; font-size:14px; color:#333; }
            QPushButton { background-color:#7CB5EC; color:#fff; border:none; border-radius:6px; padding:8px 20px; font-weight:bold; font-size:14px; }
            QPushButton:hover { background-color:#5B9BD5; }
            QPushButton:pressed { background-color:#4472C4; }
        """)
        msg.exec_()

# -------------------------------------------------------------------
# 程序主入口
# -------------------------------------------------------------------

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    setup_fcitx5_im_plugin()
    app = QApplication(sys.argv)
    viewer = FontViewerApp()
    viewer.show()
    sys.exit(app.exec_())
