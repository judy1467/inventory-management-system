# -*- coding: utf-8 -*-
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QTextEdit,
    QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QDialogButtonBox,
    QListWidget, QSizePolicy, QCheckBox
)
from data_manager import *

EMAIL_PRESETS = {
    "gmail": ("smtp.gmail.com", 587),
    "naver": ("smtp.naver.com", 587),
    "daum": ("smtp.daum.net", 465),
    "custom": ("", 587),
}

def app_stylesheet():
    return """
        QMainWindow { background: #f3f6fa; color: #111827; }
        QDialog { background: #f3f6fa; color: #111827; }
        QLabel { color: #111827; }
        QTabWidget::pane { border: 1px solid #cbd5e1; background: #ffffff; border-radius: 10px; }
        QTabBar::tab { background: #e5edf9; color: #334155; padding: 12px 24px; margin-right: 4px; border: 1px solid #cbd5e1; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }
        QTabBar::tab:selected { background: #2563eb; color: white; font-weight: 700; }
        QFrame#Card { background: #ffffff; border: 1px solid #d9e2ec; border-radius: 12px; padding: 16px; }
        QFrame[bottomGroup="true"] { background: #edf4ff; border: 1px solid #c7d8ee; border-radius: 10px; padding: 0px; }
        QLineEdit, QComboBox, QSpinBox, QTextEdit { border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; background: #ffffff; color: #111827; selection-background-color: #93c5fd; selection-color: #0f172a; min-height: 18px; font-size: 13px; }
        QLineEdit::placeholder, QTextEdit[placeholderText="true"] { color: #6b7280; }
        QPushButton { background: #3b82c4; color: white; border: none; border-radius: 8px; padding: 10px 16px; font-weight: 600; }
        QPushButton[role="secondary"] { background: #ffffff; color: #334155; border: 1px solid #cbd5e1; }
        QPushButton[role="secondary"][compact="true"] { padding: 6px 10px; min-height: 18px; font-size: 12px; }
        QPushButton[role="filter-clear"] { background: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; border-radius: 8px; padding: 6px 8px; min-width: 26px; font-weight: 700; }
        QPushButton[role="filter-clear"]:hover { background: #dbeafe; color: #1d4ed8; }
        QPushButton[role="secondary"]:hover { background: #f8fafc; border: 1px solid #94a3b8; }
        QPushButton[role="primary-strong"] { background: #3b82c4; color: white; border: 1px solid #2f6fa8; font-weight: 800; padding: 10px 18px; }
        QPushButton:hover { background: #2f6fa8; }
        QPushButton:pressed { background: #285f90; }
        QTableWidget { color: #111827; gridline-color: #cbd5e1; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; selection-background-color: #93c5fd; selection-color: #0f172a; outline: 0; }
        QTableWidget::item { padding: 2px; border: none; }
        QTableWidget::item:selected { background: #93c5fd; color: #0f172a; border: 1px solid #2563eb; }
        QTableWidget::item:selected:active { background: #93c5fd; color: #0f172a; border: 1px solid #2563eb; }
        QTableWidget::item:selected:!active { background: #bfdbfe; color: #0f172a; border: 1px solid #2563eb; }
        QTableWidget[historyTable="true"]::item { padding: 4px 6px; }
        QHeaderView::section { background: #dce6f2; color: #1e293b; padding: 11px; border: none; border-right: 1px solid #d2dce8; border-bottom: 1px solid #aebfd3; font-weight: 800; font-size: 13px; }
        QListWidget { background: #ffffff; color: #111827; border: 1px solid #cbd5e1; border-radius: 8px; selection-background-color: #93c5fd; selection-color: #0f172a; outline: 0; }
        QListWidget::item:selected { background: #93c5fd; color: #0f172a; border: 1px solid #2563eb; }
        QListWidget::item:selected:active { background: #93c5fd; color: #0f172a; border: 1px solid #2563eb; }
        QListWidget::item:selected:!active { background: #bfdbfe; color: #0f172a; border: 1px solid #2563eb; }
        QMenuBar { background: #f3f6fa; color: #111827; border-bottom: 1px solid #cbd5e1; }
        QMenuBar::item:selected { background: #dbeafe; color: #111827; }
        QMenu { background: #ffffff; color: #111827; border: 1px solid #cbd5e1; }
        QMenu::item:selected { background: #93c5fd; color: #0f172a; }
        
        QScrollBar:vertical { border: none; background: #f8fafc; width: 14px; margin: 0px 0px 0px 0px; }
        QScrollBar::handle:vertical { background: #94a3b8; min-height: 30px; border-radius: 7px; margin: 2px; }
        QScrollBar::handle:vertical:hover { background: #64748b; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; background: none; }
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        QScrollBar:horizontal { border: none; background: #f8fafc; height: 14px; margin: 0px 0px 0px 0px; }
        QScrollBar::handle:horizontal { background: #94a3b8; min-width: 30px; border-radius: 7px; margin: 2px; }
        QScrollBar::handle:horizontal:hover { background: #64748b; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; background: none; }
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal { background: none; }
    """

def build_fixed_palette():
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#f3f6fa"))
    palette.setColor(QPalette.WindowText, QColor("#111827"))
    palette.setColor(QPalette.Base, QColor("#ffffff"))
    palette.setColor(QPalette.AlternateBase, QColor("#f8fafc"))
    palette.setColor(QPalette.Text, QColor("#111827"))
    palette.setColor(QPalette.Button, QColor("#ffffff"))
    palette.setColor(QPalette.ButtonText, QColor("#111827"))
    palette.setColor(QPalette.Highlight, QColor("#93c5fd"))
    palette.setColor(QPalette.HighlightedText, QColor("#0f172a"))
    palette.setColor(QPalette.ToolTipBase, QColor("#ffffff"))
    palette.setColor(QPalette.ToolTipText, QColor("#111827"))
    return palette

def stock_filter_layout_config():
    return { "layout_mode": "row", "add_trailing_stretch": True, "item_spacing": 88, "row_spacing": 16, "button_min_width": 93, "clear_width": 20, "label_width": 28, "field_right_margin": 0, "card_spacing": 10 }

def compact_bottom_bar_layout(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)

def grouped_bottom_bar_layout(layout):
    layout.setContentsMargins(12, 3, 12, 3)
    layout.setSpacing(6)
    layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

def build_bottom_bar_group():
    group = QFrame()
    group.setProperty("bottomGroup", True)
    group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    layout = QHBoxLayout(group)
    grouped_bottom_bar_layout(layout)
    return group, layout

def set_equal_button_widths(*buttons, width_multiplier=1):
    valid_buttons = [button for button in buttons if button is not None]
    if not valid_buttons: return 0
    multiplier = max(1, to_int(width_multiplier, 1))
    for button in valid_buttons: button.ensurePolished()
    target_width = max(max(button.sizeHint().width(), button.minimumSizeHint().width()) for button in valid_buttons) * multiplier
    for button in valid_buttons: button.setFixedWidth(target_width)
    return target_width

def stock_column_widths(): return [42, 140, 140, 229, 104, 76, 81, 96, 92, 164]
def history_column_widths(): return [172, 66, 135, 135, 179, 98, 76, 92, 102, 96, 164]

def history_kind_colors(kind):
    k = str(kind or "").strip()
    if k == "입고": return "#dcfce7", "#111827"
    if k == "출고": return "#fee2e2", "#111827"
    if k == "정정": return "#e0f2fe", "#111827"
    return None

def history_kind_badge_stylesheet(kind):
    color_pair = history_kind_colors(kind)
    if not color_pair: return "background: transparent; color: #111827; font-weight: 600; padding: 0 6px;"
    bg_color, fg_color = color_pair
    return f"background: {bg_color}; color: {fg_color}; border-radius: 6px; font-weight: 700; padding: 4px 6px;"

def build_history_kind_badge(kind):
    badge = QLabel(str(kind or ""))
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(history_kind_badge_stylesheet(kind))
    return badge

class BackupCreateDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("백업 생성")
        self.setModal(True)
        self.resize(340, 180)
        
        layout = QVBoxLayout(self)
        
        guide = QLabel("원하는 백업 방식을 선택해 주세요.")
        guide.setStyleSheet("font-size: 13px; color: #475569; margin-bottom: 8px; font-weight: 600;")
        layout.addWidget(guide)
        
        self.local_check = QCheckBox("로컬 백업 (프로그램 폴더 내 백업 저장)")
        self.email_check = QCheckBox("이메일 백업 (설정된 주소로 백업 메일 발송)")
        self.local_check.setChecked(True)
        
        layout.addWidget(self.local_check)
        layout.addWidget(self.email_check)
        layout.addSpacing(12)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self.backup_btn = QPushButton("백업")
        cancel_btn = QPushButton("취소")
        cancel_btn.setProperty("role", "secondary")
        
        self.backup_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        btn_row.addWidget(self.backup_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        
    def get_selected_modes(self):
        return {
            "local": self.local_check.isChecked(),
            "email": self.email_check.isChecked()
        }

class ValuePickerDialog(QDialog):
    def __init__(self, title, values, selected_value="전체", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(340, 470)
        self.selected_value = None
        self.all_values = ["전체"] + list(values)
        layout = QVBoxLayout(self)
        guide = QLabel("하나만 선택한 뒤 적용하세요.")
        guide.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(guide)
        self.search = QLineEdit()
        self.search.setPlaceholderText("필터 값을 검색하세요")
        self.search.textChanged.connect(self.refresh_list)
        layout.addWidget(self.search)
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _: self.accept_selection())
        layout.addWidget(self.list_widget, 1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        apply_btn = QPushButton("적용")
        cancel_btn = QPushButton("취소")
        cancel_btn.setProperty("role", "secondary")
        apply_btn.clicked.connect(self.accept_selection)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.refresh_list(selected_value or "전체")

    def refresh_list(self, selected_value=None):
        current_value = selected_value if isinstance(selected_value, str) else (self.selected_value or "전체")
        filtered = filter_option_values(self.all_values, self.search.text())
        self.list_widget.clear()
        for value in filtered: self.list_widget.addItem(value)
        target = current_value or "전체"
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == target:
                self.list_widget.setCurrentRow(i)
                break
        if self.list_widget.count() > 0 and self.list_widget.currentRow() < 0:
            self.list_widget.setCurrentRow(0)

    def accept_selection(self):
        item = self.list_widget.currentItem()
        if not item:
            QMessageBox.information(self, "안내", "값을 하나 선택하세요.")
            return
        self.selected_value = item.text()
        self.accept()


class ItemPickerDialog(QDialog):
    def __init__(self, items, parent=None, title="품목 선택"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(980, 520)
        self.items = items
        self.selected_index = None
        self.stock_filter_fields = ["브랜드", "종류", "자재명", "규격", "위치"]
        self.stock_filters = {field_name: "전체" for field_name in self.stock_filter_fields}
        self.stock_filter_buttons = {}
        self.stock_filter_clear_buttons = {}
        layout = QVBoxLayout(self)

        self.search = QLineEdit()
        self.search.setPlaceholderText("브랜드, 종류, 품명, 규격, 비고, 위치 검색")
        self.search.textChanged.connect(self.refresh_table)
        self.search.returnPressed.connect(self.select_current)
        layout.addWidget(self.search)

        filter_config = stock_filter_layout_config()
        filter_wrap = QHBoxLayout()
        filter_wrap.setSpacing(filter_config["item_spacing"])
        filter_wrap.setContentsMargins(0, 0, 0, 0)
        for field_name in self.stock_filter_fields:
            field_wrap = QWidget()
            field_row = QHBoxLayout(field_wrap)
            field_row.setContentsMargins(0, 0, filter_config["field_right_margin"], 0)
            field_row.setSpacing(filter_config["row_spacing"])

            label = QLabel(FILTER_FIELD_LABELS[field_name])
            label.setFixedWidth(filter_config["label_width"])
            label.setStyleSheet("font-size: 12px; font-weight: 700; color: #475569;")
            
            button = QPushButton("전체")
            button.setProperty("role", "secondary")
            button.setProperty("compact", True)
            button.setFixedWidth(filter_config["button_min_width"])
            button.clicked.connect(lambda _=False, fn=field_name: self.open_stock_filter_picker(fn))
            
            clear_btn = QPushButton("X")
            clear_btn.setProperty("role", "filter-clear")
            clear_btn.setProperty("compact", True)
            clear_btn.setFixedWidth(filter_config["clear_width"])
            sp = clear_btn.sizePolicy()
            sp.setRetainSizeWhenHidden(True)
            clear_btn.setSizePolicy(sp)
            clear_btn.setVisible(False)
            clear_btn.clicked.connect(lambda _=False, fn=field_name: self.clear_stock_filter_field(fn))
            
            self.stock_filter_buttons[field_name] = button
            self.stock_filter_clear_buttons[field_name] = clear_btn

            field_row.addWidget(label)
            field_row.addWidget(button)
            field_row.addWidget(clear_btn)
            filter_wrap.addWidget(field_wrap)

        if filter_config.get("add_trailing_stretch"):
            filter_wrap.addStretch()
        layout.addLayout(filter_wrap)

        info_row = QHBoxLayout()
        self.count_label = QLabel("조회 품목수: 0건")
        self.count_label.setStyleSheet("color:#4b5563; font-size:13px;")
        self.filter_summary_label = QLabel("적용 필터 없음")
        self.filter_summary_label.setStyleSheet("color:#2563eb; font-size:13px; font-weight:600;")
        info_row.addWidget(self.count_label)
        info_row.addSpacing(12)
        info_row.addWidget(self.filter_summary_label)
        info_row.addStretch()
        layout.addLayout(info_row)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(["No", "브랜드", "종류", "품명", "규격", "재고", "단위", "평균단가", "위치", "비고"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(False)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.table.doubleClicked.connect(self.select_current)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        select_btn = QPushButton("선택")
        cancel_btn = QPushButton("취소")
        cancel_btn.setProperty("role", "secondary")
        select_btn.clicked.connect(self.select_current)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(select_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.refresh_filter_buttons()
        self.refresh_table()

    def filtered_items(self): return filter_stock_indexed_rows(self.items, self.search.text(), self.stock_filters)

    def refresh_filter_buttons(self):
        for field_name, button in self.stock_filter_buttons.items():
            value = self.stock_filters.get(field_name, "전체")
            button.setText(truncate_filter_label(value))
            button.setToolTip(value if value != "전체" else "")
        for field_name, clear_btn in self.stock_filter_clear_buttons.items():
            clear_btn.setVisible(self.stock_filters.get(field_name, "전체") != "전체")
        self.filter_summary_label.setText(active_filter_summary(self.stock_filters))

    def open_stock_filter_picker(self, field_name):
        values = distinct_values(self.items, field_name)
        dlg = ValuePickerDialog(f"{FILTER_FIELD_LABELS[field_name]} 필터 선택", values, self.stock_filters.get(field_name, "전체"), self)
        if not dlg.exec(): return
        self.stock_filters[field_name] = dlg.selected_value or "전체"
        self.refresh_filter_buttons()
        self.refresh_table()

    def clear_stock_filter_field(self, field_name):
        self.stock_filters = clear_stock_filter(self.stock_filters, field_name)
        self.refresh_filter_buttons()
        self.refresh_table()

    def refresh_table(self):
        rows = self.filtered_items()
        self.table.setRowCount(len(rows))
        self.count_label.setText(f"조회 품목수: {len(rows)}건")
        widths = [50, 143, 143, 221, 110, 85, 81, 95, 90, 180]
        for i, w in enumerate(widths): self.table.setColumnWidth(i, w)

        for row_no, (source_index, row) in enumerate(rows):
            values = [str(row_no + 1), row.get("브랜드", ""), row.get("종류", ""), row.get("자재명", ""), row.get("규격", ""), row.get("재고", "0"), row.get("단위", ""), f"{to_int(row.get('평균단가', 0)):,}", row.get("위치", ""), row.get("비고", "")]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, source_index)
                if col in (5, 6, 7): item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col in (0, 1, 2, 4, 8): item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row_no, col, item)
        
        last_idx = self.table.columnCount() - 1
        self.table.resizeColumnToContents(last_idx)
        final_w = max(self.table.columnWidth(last_idx) + 16, 150)
        self.table.setColumnWidth(last_idx, final_w)

    def select_current(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "안내", "품목을 선택하세요.")
            return
        item = self.table.item(row, 0)
        if item:
            self.selected_index = item.data(Qt.UserRole)
            self.accept()


class ItemDialog(QDialog):
    def __init__(self, parent=None, data=None, new_item=False):
        super().__init__(parent)
        self.setWindowTitle("신규 품목 등록" if new_item else "자재 등록 / 수정")
        self.setModal(True)
        self.resize(460, 430)

        self.inputs = {}
        self.selectable_fields = ["브랜드", "종류", "자재명", "규격", "단위", "위치"]
        stock_rows = getattr(parent, "stock_rows", []) if parent is not None else []
        self.saved_field_values = { field_name: distinct_values(stock_rows, field_name) for field_name in self.selectable_fields }
        layout = QVBoxLayout(self)
        form = QFormLayout()

        fields = [ ("브랜드", QLineEdit), ("종류", QLineEdit), ("자재명", QLineEdit), ("규격", QLineEdit), ("단위", QLineEdit), ("재고", QSpinBox), ("평균단가", QSpinBox), ("위치", QLineEdit), ("비고", QTextEdit) ]

        for label, widget_cls in fields:
            widget = widget_cls()
            if isinstance(widget, QSpinBox):
                widget.setRange(0, 999999999)
                widget.setGroupSeparatorShown(True)
            if isinstance(widget, QTextEdit): widget.setFixedHeight(80)
            if new_item and label in ("재고", "평균단가"):
                widget.setEnabled(False)
                widget.setStyleSheet("background: #e5e7eb; color: #9ca3af;")
            self.inputs[label] = widget
            if label in self.selectable_fields:
                row_wrap = QWidget()
                row_layout = QHBoxLayout(row_wrap)
                row_layout.setContentsMargins(0, 0, 0, 0)
                row_layout.setSpacing(8)
                select_btn = QPushButton("선택")
                select_btn.setProperty("role", "secondary")
                select_btn.setProperty("compact", True)
                select_btn.clicked.connect(lambda _=False, fn=label: self.open_saved_value_picker(fn))
                row_layout.addWidget(widget, 1)
                row_layout.addWidget(select_btn)
                form.addRow(label, row_wrap)
            else:
                form.addRow(label, widget)

        layout.addLayout(form)
        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        if data:
            for key, widget in self.inputs.items():
                val = data.get(key, "")
                if isinstance(widget, QLineEdit): widget.setText(val)
                elif isinstance(widget, QSpinBox): widget.setValue(to_int(val))
                elif isinstance(widget, QTextEdit): widget.setPlainText(val)

    def open_saved_value_picker(self, field_name):
        values = self.saved_field_values.get(field_name, [])
        if not values:
            QMessageBox.information(self, "안내", f"저장된 {field_name} 값이 없습니다.")
            return
        current = self.inputs[field_name].text().strip() if field_name in self.inputs else ""
        dlg = ValuePickerDialog(f"{field_name} 선택", values, current or "전체", self)
        if dlg.exec():
            selected = dlg.selected_value or ""
            if selected == "전체": selected = ""
            if isinstance(self.inputs.get(field_name), QLineEdit):
                self.inputs[field_name].setText(selected)

    def get_data(self):
        result = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit): result[key] = widget.text().strip()
            elif isinstance(widget, QSpinBox): result[key] = str(widget.value())
            elif isinstance(widget, QTextEdit): result[key] = widget.toPlainText().strip()
        return result


class InOutDialog(QDialog):
    def __init__(self, title, parent=None, item=None, is_outbound=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(380, 260)
        self.item = item or {}

        layout = QVBoxLayout(self)
        lines = [ f"브랜드: {self.item.get('브랜드','')}", f"종류: {self.item.get('종류','')}", f"품명: {self.item.get('자재명','')} ({self.item.get('규격','')})", f"재고: {self.item.get('재고','0')} {self.item.get('단위','')}" ]
        if is_outbound:
            avg = to_int(self.item.get("평균단가", 0))
            if avg > 0: lines.append(f"현재 평균원가: {avg:,}원")
        info = QLabel("\n".join(lines))
        info.setStyleSheet("font-size: 13px; line-height: 1.6;")
        layout.addWidget(info)

        form = QFormLayout()
        self.qty = QSpinBox()
        self.qty.setRange(1, 999999999)
        self.price = QSpinBox()
        self.price.setRange(0, 999999999)
        self.staff = QLineEdit()
        self.note = QLineEdit()
        form.addRow("수량", self.qty)
        form.addRow("단가", self.price)
        form.addRow("담당자", self.staff)
        form.addRow("비고", self.note)
        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def get_data(self):
        return { "수량": self.qty.value(), "단가": self.price.value(), "담당자": self.staff.text().strip(), "비고": self.note.text().strip() }


class EmailConfigDialog(QDialog):
    def __init__(self, parent=None, cfg=None):
        super().__init__(parent)
        self.setWindowTitle("이메일 백업 설정")
        self.setModal(True)
        self.resize(440, 340)
        self.cfg = cfg or {}
        layout = QVBoxLayout(self)

        guide = QLabel("매일 첫 실행시 자동 이메일 백업을 보냅니다.")
        guide.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(guide)

        form = QFormLayout()
        self.provider = QComboBox()
        self.provider.addItems(["Gmail", "Naver (네이버)", "Daum (다음)", "직접입력"])
        self.provider.currentIndexChanged.connect(self.on_provider_changed)
        self.smtp_server = QLineEdit()
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_port.setValue(587)
        self.smtp_port.setGroupSeparatorShown(False)
        self.sender_email = QLineEdit()
        self.sender_email.setPlaceholderText("발송 이메일")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("앱 비밀번호")

        form.addRow("제공자", self.provider)
        form.addRow("SMTP 서버", self.smtp_server)
        form.addRow("SMTP 포트", self.smtp_port)
        form.addRow("이메일", self.sender_email)
        form.addRow("비밀번호", self.password)
        layout.addLayout(form)

        test_btn = QPushButton("테스트 발송")
        test_btn.setProperty("role", "secondary")
        test_btn.clicked.connect(self.send_test)
        layout.addWidget(test_btn)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        if self.cfg: self.load_cfg(self.cfg)

    def load_cfg(self, cfg):
        provider = cfg.get("provider", "custom")
        provider_map = {"gmail": 0, "naver": 1, "daum": 2, "custom": 3}
        self.provider.setCurrentIndex(provider_map.get(provider, 3))
        self.smtp_server.setText(cfg.get("smtp_server", ""))
        self.smtp_port.setValue(cfg.get("smtp_port", 587))
        self.sender_email.setText(cfg.get("sender", ""))
        self.password.setText(cfg.get("password", ""))

    def on_provider_changed(self, idx):
        names = ["gmail", "naver", "daum", "custom"]
        key = names[idx] if 0 <= idx < len(names) else "custom"
        server, port = EMAIL_PRESETS.get(key, ("", 587))
        if server:
            self.smtp_server.setText(server)
            self.smtp_port.setValue(port)

    def get_cfg(self):
        names = ["gmail", "naver", "daum", "custom"]
        return {
            "provider": names[self.provider.currentIndex()],
            "smtp_server": self.smtp_server.text().strip(),
            "smtp_port": self.smtp_port.value(),
            "sender": self.sender_email.text().strip(),
            "password": self.password.text().strip(),
            "receiver": self.sender_email.text().strip(),
        }

    def send_test(self):
        cfg = self.get_cfg()
        try:
            send_backup_email(cfg)
            QMessageBox.information(self, "성공", "테스트 메일이 발송되었습니다.")
        except Exception as e:
            QMessageBox.critical(self, "실패", f"메일 발송에 실패했습니다.\n{str(e)}")
