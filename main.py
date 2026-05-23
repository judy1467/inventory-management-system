# -*- coding: utf-8 -*-
import sys
import os
import re
import shutil
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QFileDialog
)

from data_manager import *
from ui_components import *

class IMSInventoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("다모다웰딩 재고관리 시스템")
        self.resize(1480, 900)
        self.setMinimumSize(1180, 680)
        self.stock_rows, self.history_rows = [], []
        self.current_page, self.page_size = 1, STOCK_PAGE_SIZE
        self.current_history_page, self.history_page_size = 1, HISTORY_PAGE_SIZE
        
        self.stock_filter_fields = ["브랜드", "종류", "자재명", "규격", "위치"]
        self.stock_filters = {f: "전체" for f in self.stock_filter_fields}
        self.stock_filter_buttons, self.stock_filter_clear_buttons = {}, {}
        
        self.history_filter_fields = ["브랜드", "종류", "자재명", "규격", "위치"]
        self.history_filters = {f: "전체" for f in self.history_filter_fields}
        self.history_filter_buttons, self.history_filter_clear_buttons = {}, {}

        self._stock_search_timer = QTimer(self)
        self._stock_search_timer.setSingleShot(True)
        self._stock_search_timer.timeout.connect(self.on_stock_search_changed)
        
        self._history_search_timer = QTimer(self)
        self._history_search_timer.setSingleShot(True)
        self._history_search_timer.timeout.connect(self.on_history_filters_changed)

        self.init_ui()
        self.load_all_data()
        self.refresh_all()
        QTimer.singleShot(500, self.check_and_send_daily_backup)

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self.build_stock_tab(), "재고현황")
        self.tabs.addTab(self.build_inout_tab(), "입출고관리")
        self.tabs.addTab(self.build_history_tab(), "입출고기록")
        root.addWidget(self.tabs)

        self.apply_styles()
        self.build_menu()

    def section_title(self, title, desc=""):
        wrap = QWidget()
        lay = QVBoxLayout(wrap)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(2)
        h1 = QLabel(title)
        h1.setStyleSheet("font-size: 24px; font-weight: 700; color: #1f2937;")
        lay.addWidget(h1)
        if desc:
            sub = QLabel(desc)
            sub.setStyleSheet("font-size: 13px; color: #6b7280;")
            lay.addWidget(sub)
        return wrap

    def build_stock_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.addWidget(self.section_title("재고현황 리스트"))

        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        toolbar_card_layout = QVBoxLayout(toolbar_card)
        toolbar_card_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_card_layout.setSpacing(stock_filter_layout_config()["card_spacing"])

        toolbar_row = QWidget()
        toolbar = QHBoxLayout(toolbar_row)
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(8)
        self.stock_search = QLineEdit()
        self.stock_search.setPlaceholderText("브랜드, 종류, 품명, 규격, 비고, 위치로 빠르게 검색할 수 있습니다.")
        self.stock_search.textChanged.connect(lambda: self._stock_search_timer.start(300))
        reset_btn = QPushButton("초기화")
        reset_btn.setProperty("role", "secondary")
        reset_btn.clicked.connect(self.reset_stock_search)
        toolbar.addWidget(self.stock_search, 1)
        toolbar.addWidget(reset_btn)
        toolbar_card_layout.addWidget(toolbar_row)

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
        toolbar_card_layout.addLayout(filter_wrap)

        info = QHBoxLayout()
        self.stock_count_label = QLabel("등록 품목수: 0건")
        self.stock_count_label.setStyleSheet("color:#4b5563; font-size:13px;")
        self.stock_filter_summary_label = QLabel("적용 필터 없음")
        self.stock_filter_summary_label.setStyleSheet("color:#2563eb; font-size:13px; font-weight:600;")
        info.addWidget(self.stock_count_label)
        info.addSpacing(12)
        info.addWidget(self.stock_filter_summary_label)
        info.addStretch()
        toolbar_card_layout.addLayout(info)

        layout.addWidget(toolbar_card)

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(10)
        self.stock_table.setHorizontalHeaderLabels(["No", "브랜드", "종류", "품명", "규격", "재고", "단위", "평균단가", "위치", "비고"])
        self.prepare_table(self.stock_table)
        self.stock_table.doubleClicked.connect(lambda: self.edit_selected_item())
        layout.addWidget(self.stock_table, 1)

        bottom_row = QWidget()
        bottom = QHBoxLayout(bottom_row)
        compact_bottom_bar_layout(bottom)
        self.page_label = QLabel(stock_pagination_summary(1, 1))
        self.page_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.page_jump_input = QLineEdit()
        self.page_jump_input.setPlaceholderText("페이지")
        self.page_jump_input.setFixedWidth(64)
        self.page_jump_input.setAlignment(Qt.AlignCenter)
        self.page_jump_input.setValidator(QIntValidator(1, 999999, self))
        self.page_jump_input.returnPressed.connect(self.go_to_input_page)
        
        page_jump_btn = QPushButton("이동")
        page_jump_btn.setProperty("role", "secondary")
        page_jump_btn.clicked.connect(self.go_to_input_page)
        
        prev_btn = QPushButton("이전")
        next_btn = QPushButton("다음")
        prev_btn.setProperty("role", "secondary")
        next_btn.setProperty("role", "secondary")
        prev_btn.clicked.connect(self.prev_page)
        next_btn.clicked.connect(self.next_page)
        
        edit_btn = QPushButton("변경")
        edit_btn.setProperty("role", "primary-strong")
        edit_btn.clicked.connect(self.edit_selected_item)
        del_btn = QPushButton("삭제")
        del_btn.setProperty("role", "secondary")
        del_btn.clicked.connect(self.delete_selected_item)
        
        page_group, page_group_layout = build_bottom_bar_group()
        page_group_layout.addWidget(self.page_label)
        page_group_layout.addWidget(self.page_jump_input)
        page_group_layout.addWidget(page_jump_btn)
        set_equal_button_widths(page_jump_btn, prev_btn, next_btn, edit_btn, del_btn)

        bottom.addWidget(page_group)
        bottom.addWidget(prev_btn)
        bottom.addWidget(next_btn)
        bottom.addStretch()
        bottom.addWidget(edit_btn)
        bottom.addWidget(del_btn)
        layout.addWidget(bottom_row)

        return tab

    def build_inout_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.addWidget(self.section_title("입출고관리"))

        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        action_grid = QGridLayout()
        action_grid.setContentsMargins(0, 0, 0, 0)
        action_grid.setHorizontalSpacing(14)
        action_grid.setVerticalSpacing(10)

        inbound_box = QFrame()
        inbound_box.setObjectName("Card")
        inbound_layout = QVBoxLayout(inbound_box)
        inbound_layout.setContentsMargins(16, 16, 16, 16)
        inbound_layout.setSpacing(8)
        inbound_title = QLabel("입고 등록")
        inbound_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1f2937;")
        new_item_btn = QPushButton(INOUT_NEW_ITEM_BUTTON_TEXT)
        new_item_btn.setProperty("role", "secondary")
        new_item_btn.clicked.connect(self.add_new_item_with_inbound)
        inbound_btn = QPushButton("등록된 품목 선택 후 입고 등록")
        inbound_btn.setProperty("role", "primary-strong")
        inbound_btn.clicked.connect(self.process_inbound_selected)
        inbound_layout.addWidget(inbound_title)
        inbound_layout.addSpacing(4)
        inbound_layout.addWidget(inbound_btn)
        inbound_layout.addWidget(new_item_btn)
        inbound_layout.addStretch()

        outbound_box = QFrame()
        outbound_box.setObjectName("Card")
        outbound_layout = QVBoxLayout(outbound_box)
        outbound_layout.setContentsMargins(16, 16, 16, 16)
        outbound_layout.setSpacing(8)
        outbound_title = QLabel("출고 등록")
        outbound_title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1f2937;")
        outbound_btn = QPushButton("등록된 품목 선택 후 출고 등록")
        outbound_btn.setProperty("role", "primary-strong")
        outbound_btn.clicked.connect(self.process_outbound_selected)
        outbound_layout.addWidget(outbound_title)
        outbound_layout.addSpacing(4)
        outbound_layout.addWidget(outbound_btn)
        outbound_layout.addStretch()

        action_grid.addWidget(inbound_box, 0, 0)
        action_grid.addWidget(outbound_box, 0, 1)
        card_layout.addLayout(action_grid)
        layout.addWidget(card)
        layout.addStretch()
        return tab

    def build_history_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.addWidget(self.section_title("입출고기록"))

        toolbar_card = QFrame()
        toolbar_card.setObjectName("Card")
        toolbar_card_layout = QVBoxLayout(toolbar_card)
        toolbar_card_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_card_layout.setSpacing(stock_filter_layout_config()["card_spacing"])

        top_row = QWidget()
        top = QHBoxLayout(top_row)
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(8)
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("브랜드, 종류, 품명, 규격, 비고, 위치로 빠르게 검색할 수 있습니다.")
        self.history_search.textChanged.connect(lambda: self._history_search_timer.start(300))
        self.history_kind = QComboBox()
        self.history_kind.addItems(["전체", "입고", "출고", "정정"])
        self.history_kind.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.history_kind.setMinimumContentsLength(4)
        self.history_kind.currentTextChanged.connect(self.on_history_filters_changed)
        reset_btn = QPushButton("초기화")
        reset_btn.setProperty("role", "secondary")
        reset_btn.clicked.connect(self.reset_history_search)
        top.addWidget(self.history_search, 1)
        top.addWidget(self.history_kind)
        top.addWidget(reset_btn)
        toolbar_card_layout.addWidget(top_row)

        filter_config = stock_filter_layout_config()
        filter_wrap = QHBoxLayout()
        filter_wrap.setSpacing(filter_config["item_spacing"])
        filter_wrap.setContentsMargins(0, 0, 0, 0)
        for field_name in self.history_filter_fields:
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
            button.clicked.connect(lambda _=False, fn=field_name: self.open_history_filter_picker(fn))

            clear_btn = QPushButton("X")
            clear_btn.setProperty("role", "filter-clear")
            clear_btn.setProperty("compact", True)
            clear_btn.setFixedWidth(filter_config["clear_width"])
            sp = clear_btn.sizePolicy()
            sp.setRetainSizeWhenHidden(True)
            clear_btn.setSizePolicy(sp)
            clear_btn.setVisible(False)
            clear_btn.clicked.connect(lambda _=False, fn=field_name: self.clear_history_filter_field(fn))

            self.history_filter_buttons[field_name] = button
            self.history_filter_clear_buttons[field_name] = clear_btn

            field_row.addWidget(label)
            field_row.addWidget(button)
            field_row.addWidget(clear_btn)
            filter_wrap.addWidget(field_wrap)

        if filter_config.get("add_trailing_stretch"):
            filter_wrap.addStretch()
        toolbar_card_layout.addLayout(filter_wrap)

        info = QHBoxLayout()
        self.history_count_label = QLabel("조회 이력수: 0건")
        self.history_count_label.setStyleSheet("color:#4b5563; font-size:13px;")
        self.history_filter_summary_label = QLabel("적용 필터 없음")
        self.history_filter_summary_label.setStyleSheet("color:#2563eb; font-size:13px; font-weight:600;")
        info.addWidget(self.history_count_label)
        info.addSpacing(12)
        info.addWidget(self.history_filter_summary_label)
        info.addStretch()
        toolbar_card_layout.addLayout(info)
        layout.addWidget(toolbar_card)

        self.history_table = QTableWidget()
        self.history_table.setProperty("historyTable", True)
        self.history_table.setColumnCount(11)
        self.history_table.setHorizontalHeaderLabels(["일시", "구분", "브랜드", "종류", "품명", "규격", "수량", "단가", "금액", "위치", "비고"])
        self.prepare_table(self.history_table)
        layout.addWidget(self.history_table, 1)

        bottom_row = QWidget()
        bottom = QHBoxLayout(bottom_row)
        compact_bottom_bar_layout(bottom)
        self.history_page_label = QLabel(stock_pagination_summary(1, 1))
        self.history_page_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.history_page_jump_input = QLineEdit()
        self.history_page_jump_input.setPlaceholderText("페이지")
        self.history_page_jump_input.setFixedWidth(64)
        self.history_page_jump_input.setAlignment(Qt.AlignCenter)
        self.history_page_jump_input.setValidator(QIntValidator(1, 999999, self))
        self.history_page_jump_input.returnPressed.connect(self.go_to_input_history_page)
        history_page_jump_btn = QPushButton("이동")
        history_page_jump_btn.setProperty("role", "secondary")
        history_page_jump_btn.clicked.connect(self.go_to_input_history_page)
        history_prev_btn = QPushButton("이전")
        history_next_btn = QPushButton("다음")
        history_prev_btn.setProperty("role", "secondary")
        history_next_btn.setProperty("role", "secondary")
        history_prev_btn.clicked.connect(self.prev_history_page)
        history_next_btn.clicked.connect(self.next_history_page)
        
        history_page_group, history_page_group_layout = build_bottom_bar_group()
        history_page_group_layout.addWidget(self.history_page_label)
        history_page_group_layout.addWidget(self.history_page_jump_input)
        history_page_group_layout.addWidget(history_page_jump_btn)
        set_equal_button_widths(history_page_jump_btn, history_prev_btn, history_next_btn)

        bottom.addWidget(history_page_group)
        bottom.addWidget(history_prev_btn)
        bottom.addWidget(history_next_btn)
        bottom.addStretch()
        
        history_revert_btn = QPushButton("되돌리기")
        history_revert_btn.setProperty("role", "secondary")
        history_revert_btn.clicked.connect(self.revert_selected_history)
        set_equal_button_widths(history_revert_btn)
        bottom.addWidget(history_revert_btn)
        
        layout.addWidget(bottom_row)
        return tab

    def build_menu(self):
        menu = self.menuBar()
        backup_menu = menu.addMenu("백업")
        
        create_backup_action = QAction("백업 생성", self)
        create_backup_action.triggered.connect(self.open_create_backup_dialog)
        backup_menu.addAction(create_backup_action)
        
        email_cfg_action = QAction("이메일 백업 설정", self)
        email_cfg_action.triggered.connect(self.open_email_config)
        backup_menu.addAction(email_cfg_action)

    def apply_styles(self):
        app = QApplication.instance()
        if app: app.setPalette(build_fixed_palette())
        self.setStyleSheet(app_stylesheet())

    def prepare_table(self, table: QTableWidget):
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(36)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        
        table.horizontalHeader().setStretchLastSection(False)
        table.setWordWrap(False)
        table.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setShowGrid(True)

    def adjust_last_column_width(self, table: QTableWidget):
        last_idx = table.columnCount() - 1
        if last_idx < 0: return
        table.resizeColumnToContents(last_idx)
        content_w = table.columnWidth(last_idx) + 16
        viewport_w = table.viewport().width()
        used_w = sum(table.columnWidth(i) for i in range(last_idx))
        remaining_w = viewport_w - used_w
        table.setColumnWidth(last_idx, max(content_w, remaining_w, 150))

    def load_all_data(self):
        ensure_files()
        self.stock_rows = read_csv(STOCK_CSV)
        self.history_rows = read_csv(HISTORY_CSV)
        self.refresh_stock_filter_buttons()

    def refresh_stock_filter_buttons(self):
        for field_name, button in self.stock_filter_buttons.items():
            value = self.stock_filters.get(field_name, "전체")
            button.setText(truncate_filter_label(value))
            button.setToolTip(value if value != "전체" else "")
        for field_name, clear_btn in self.stock_filter_clear_buttons.items():
            clear_btn.setVisible(self.stock_filters.get(field_name, "전체") != "전체")
        self.stock_filter_summary_label.setText(active_filter_summary(self.stock_filters))

    def refresh_history_filter_buttons(self):
        for field_name, button in self.history_filter_buttons.items():
            value = self.history_filters.get(field_name, "전체")
            button.setText(truncate_filter_label(value))
            button.setToolTip(value if value != "전체" else "")
        for field_name, clear_btn in self.history_filter_clear_buttons.items():
            clear_btn.setVisible(self.history_filters.get(field_name, "전체") != "전체")
        self.history_filter_summary_label.setText(active_filter_summary(self.history_filters))

    def reset_stock_search(self):
        self.stock_search.clear()
        self.stock_filters = {f: "전체" for f in self.stock_filter_fields}
        self.refresh_stock_filter_buttons()
        self.current_page = 1
        self.refresh_stock_table()

    def reset_history_search(self):
        self.history_search.clear()
        self.history_kind.setCurrentText("전체")
        self.history_filters = {f: "전체" for f in self.history_filter_fields}
        self.refresh_history_filter_buttons()
        self.current_history_page = 1
        self.refresh_history_table()

    def on_stock_search_changed(self):
        self.current_page = 1
        self.refresh_stock_table()

    def on_history_filters_changed(self):
        self.current_history_page = 1
        self.refresh_history_table()

    def open_history_filter_picker(self, field_name):
        values = distinct_history_values(self.history_rows, field_name, self.stock_rows)
        dlg = ValuePickerDialog(f"{FILTER_FIELD_LABELS[field_name]} 필터 선택", values, self.history_filters.get(field_name, "전체"), self)
        if not dlg.exec(): return
        self.history_filters[field_name] = dlg.selected_value or "전체"
        self.refresh_history_filter_buttons()
        self.current_history_page = 1
        self.refresh_history_table()

    def clear_history_filter_field(self, field_name):
        self.history_filters = clear_stock_filter(self.history_filters, field_name)
        self.refresh_history_filter_buttons()
        self.current_history_page = 1
        self.refresh_history_table()

    def open_stock_filter_picker(self, field_name):
        values = distinct_values(self.stock_rows, field_name)
        dlg = ValuePickerDialog(f"{FILTER_FIELD_LABELS[field_name]} 필터 선택", values, self.stock_filters.get(field_name, "전체"), self)
        if not dlg.exec(): return
        self.stock_filters[field_name] = dlg.selected_value or "전체"
        self.refresh_stock_filter_buttons()
        self.current_page = 1
        self.refresh_stock_table()

    def clear_stock_filter_field(self, field_name):
        self.stock_filters = clear_stock_filter(self.stock_filters, field_name)
        self.refresh_stock_filter_buttons()
        self.current_page = 1
        self.refresh_stock_table()

    def refresh_all(self):
        self.refresh_stock_table()
        self.refresh_history_table()

    def refresh_stock_table(self):
        indexed_rows = filter_stock_indexed_rows(self.stock_rows, self.stock_search.text(), self.stock_filters.copy())
        total = len(indexed_rows)
        pages = stock_total_pages(total, self.page_size)
        self.current_page = clamp_page_number(self.current_page, pages)
        start = (self.current_page - 1) * self.page_size
        page_rows = indexed_rows[start:start + self.page_size]

        self.stock_table.setRowCount(len(page_rows))
        widths = stock_column_widths()
        for i, w in enumerate(widths): self.stock_table.setColumnWidth(i, w)

        for i, (source_index, row) in enumerate(page_rows):
            no = start + i + 1
            stock_qty = to_int(row.get("재고", 0))
            is_low_stock = stock_qty <= 5
            values = [str(no), row.get("브랜드", ""), row.get("종류", ""), row.get("자재명", ""), row.get("규격", ""), str(stock_qty), row.get("단위", ""), f"{to_int(row.get('평균단가', 0)):,}", row.get("위치", ""), row.get("비고", "")]

            for col, val in enumerate(values):
                self.stock_table.removeCellWidget(i, col)
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, source_index)
                default_bg = QColor("#f8fafc") if i % 2 == 1 else QColor("#ffffff")
                item.setBackground(default_bg)
                if col in (1, 3): item.setForeground(QColor("#2563eb"))
                if col in (5, 6, 7): item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col in (0, 1, 2, 4, 8): item.setTextAlignment(Qt.AlignCenter)
                self.stock_table.setItem(i, col, item)

                if col == 5 and is_low_stock:
                    bg_label = QLabel(str(stock_qty))
                    bg_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    bg_label.setStyleSheet("background-color: #fee2e2; color: #111827; font-weight: bold; padding-right: 4px;")
                    self.stock_table.setCellWidget(i, col, bg_label)

        self.page_label.setText(stock_pagination_summary(self.current_page, pages))
        self.page_jump_input.setText(str(self.current_page))
        self.stock_count_label.setText(f"등록 품목수: {total}건")
        self.adjust_last_column_width(self.stock_table)

    def refresh_history_table(self):
        rows = filter_history_rows(self.history_rows, self.history_search.text(), self.history_kind.currentText(), self.history_filters, self.stock_rows)
        rows = list(reversed(rows))
        total = len(rows)
        pages = stock_total_pages(total, self.history_page_size)
        self.current_history_page = clamp_page_number(self.current_history_page, pages)
        start = (self.current_history_page - 1) * self.history_page_size
        page_rows = rows[start:start + self.history_page_size]

        self.history_table.setRowCount(len(page_rows))
        widths = history_column_widths()
        for i, w in enumerate(widths): self.history_table.setColumnWidth(i, w)

        location_lookup = build_stock_location_lookup(self.stock_rows)
        for i, row in enumerate(page_rows):
            kind = row.get("구분", "")
            if kind == "입고": row_bg = QColor("#dcfce7")
            elif kind == "출고": row_bg = QColor("#fee2e2")
            elif kind == "정정": row_bg = QColor("#e0f2fe")
            else: row_bg = QColor("#f8fafc") if i % 2 == 1 else QColor("#ffffff")
            
            vals = [row.get("일시", ""), row.get("구분", ""), row.get("브랜드", ""), row.get("종류", ""), row.get("자재명", ""), row.get("규격", ""), row.get("수량", ""), f"{to_int(row.get('단가', 0)):,}", f"{to_int(row.get('금액', 0)):,}", history_field_value(row, "위치", location_lookup), row.get("비고", "")]
            for j, val in enumerate(vals):
                item = QTableWidgetItem(val)
                item.setBackground(row_bg)
                if j == 0: item.setData(Qt.UserRole, row)
                if j == 1:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setData(Qt.UserRole, row.get("구분", ""))
                elif j in (6, 7, 8): item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif j in (0, 2, 3, 4, 5, 9): item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(i, j, item)
                if j == 1: self.history_table.setCellWidget(i, j, build_history_kind_badge(row.get("구분", "")))

        self.history_page_label.setText(stock_pagination_summary(self.current_history_page, pages))
        self.history_page_jump_input.setText(str(self.current_history_page))
        self.history_count_label.setText(f"조회 이력수: {total}건")
        self.adjust_last_column_width(self.history_table)

    def get_selected_index(self):
        row = self.stock_table.currentRow()
        if row < 0: return None
        item = self.stock_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def get_selected_item(self):
        index = self.get_selected_index()
        return self.stock_rows[index] if index is not None and 0 <= index < len(self.stock_rows) else None

    def go_to_page(self, page_number):
        self.current_page = to_int(page_number, 1)
        self.refresh_stock_table()

    def go_to_input_page(self):
        text = self.page_jump_input.text().strip()
        if not text:
            self.page_jump_input.setText(str(self.current_page))
            return
        self.go_to_page(text)

    def prev_page(self): self.go_to_page(self.current_page - 1)
    def next_page(self): self.go_to_page(self.current_page + 1)

    def go_to_history_page(self, page_number):
        self.current_history_page = to_int(page_number, 1)
        self.refresh_history_table()

    def go_to_input_history_page(self):
        text = self.history_page_jump_input.text().strip()
        if not text:
            self.history_page_jump_input.setText(str(self.current_history_page))
            return
        self.go_to_history_page(text)

    def prev_history_page(self): self.go_to_history_page(self.current_history_page - 1)
    def next_history_page(self): self.go_to_history_page(self.current_history_page + 1)

    def add_new_item_with_inbound(self):
        item_dlg = ItemDialog(self, new_item=True)
        if not item_dlg.exec(): return
        item_data = item_dlg.get_data()
        
        required_item_fields = {"브랜드": "브랜드", "종류": "종류", "자재명": "품명", "단위": "단위", "위치": "위치"}
        missing_fields = [label for key, label in required_item_fields.items() if not item_data.get(key, "").strip()]
        if missing_fields:
            QMessageBox.warning(self, "필수 입력 확인", f"다음 항목을 입력해주세요:\n• {', '.join(missing_fields)}")
            return

        # 🔥 추가된 방어 로직: 자재명, 브랜드, 종류, 규격이 모두 같은 품목이 있는지 검사
        new_key = stock_identity_key(item_data)
        for row in self.stock_rows:
            if stock_identity_key(row) == new_key:
                QMessageBox.warning(
                    self, 
                    "중복 등록 차단", 
                    f"장부에 이미 동일한 품목이 존재합니다.\n\n"
                    f"품명: {new_key[0]}\n브랜드: {new_key[1]}\n종류: {new_key[2]}\n규격: {new_key[3]}\n\n"
                    f"새로 등록하지 마시고, 메인 화면의 [등록된 품목 선택 후 입고 등록] 버튼을 이용해 수량만 더해주세요."
                )
                return

        inout_dlg = InOutDialog(NEW_ITEM_INBOUND_DIALOG_TITLE, self, item_data)
        if not inout_dlg.exec(): return
        inbound_data = inout_dlg.get_data()
        
        if inbound_data.get("수량", 0) <= 0:
            QMessageBox.warning(self, "필수 입력 확인", "수량을 1개 이상 입력해주세요.")
            return
        if inbound_data.get("단가", 0) <= 0:
            QMessageBox.warning(self, "필수 입력 확인", "단가를 입력해주세요.")
            return

        create_new_item_inbound(self.stock_rows, self.history_rows, item_data, inbound_data)
        try:
            write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
            write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"입출고 기록 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        self.refresh_all()
        QMessageBox.information(self, "완료", "신규 자재 입고가 등록되었습니다.")

    def edit_selected_item(self):
        item = self.get_selected_item()
        if not item:
            QMessageBox.information(self, "안내", "수정할 자재를 먼저 선택하세요.")
            return
            
        old_data = item.copy()  # 변경 전 원본 데이터 전체 백업
        
        dlg = ItemDialog(self, item)
        if dlg.exec():
            new_data = dlg.get_data()
            if not new_data.get("자재명", "").strip():
                QMessageBox.warning(self, "확인", "품명은 필수입니다.")
                return
            
            # 변경된 항목이 하나라도 있는지 확인
            has_changes = False
            for k in ["브랜드", "종류", "자재명", "규격", "단위", "재고", "평균단가", "위치", "비고"]:
                if str(old_data.get(k, "")).strip() != str(new_data.get(k, "")).strip():
                    has_changes = True
                    break
                    
            if has_changes:
                apply_correction_to_history(self.history_rows, old_data, new_data)
                
            item.update(new_data)
            try:
                write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
                write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", f"저장 중 오류가 발생했습니다:\n{str(e)}")
                return
            self.refresh_all()
            QMessageBox.information(self, "완료", "자재 정보가 수정되었으며 변경 이력이 장부에 기록되었습니다.")

    def delete_selected_item(self):
        index = self.get_selected_index()
        if index is None:
            QMessageBox.information(self, "안내", "삭제할 자재를 먼저 선택하세요.")
            return
            
        item = self.stock_rows[index]
        item_name = item.get("자재명", "")
        current_qty = to_int(item.get("재고", 0))
        
        # 🔥 추가된 유효성 검사: 재고가 0보다 크면 삭제 원천 차단
        if current_qty > 0:
            QMessageBox.warning(
                self, 
                "삭제 불가", 
                f"품목: {item_name}\n현재 재고: {current_qty}개\n\n재고가 남아있는 품목은 삭제할 수 없습니다.\n먼저 출고 처리하여 재고를 0으로 만들어주세요."
            )
            return

        reply = QMessageBox.question(
            self, "삭제 확인", 
            f"품목: {item_name}\n경고: 이 품목을 삭제하면 되돌릴 수 없습니다.\n정말로 삭제하시겠습니까?", 
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        if reply != QMessageBox.Yes: return
        
        del self.stock_rows[index]
        try:
            write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"재고 목록 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
            
        self.current_page = 1
        self.refresh_all()
        QMessageBox.information(self, "완료", "선택한 품목이 장부에서 삭제되었습니다.")

    def get_selected_history_index(self):
        row = self.history_table.currentRow()
        if row < 0: return None
        item = self.history_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def get_selected_history_row(self):
        item = self.history_table.item(self.history_table.currentRow(), 0)
        return item.data(Qt.UserRole) if item else None

    def open_create_backup_dialog(self):
        dlg = BackupCreateDialog(self)
        if not dlg.exec():
            return
            
        modes = dlg.get_selected_modes()
        if not modes["local"] and not modes["email"]:
            QMessageBox.information(self, "안내", "선택된 백업 방식이 없습니다.")
            return
            
        local_success = False
        email_success = False
        
        # 1. 로컬 백업 실행 (경로 수정됨)
        if modes["local"]:
            try:
                # 🔥 먼저 프로그램 폴더 안에 'backup' 폴더를 생성(존재하면 패스)
                backup_base_dir = os.path.join(BASE_DIR, "backup")
                os.makedirs(backup_base_dir, exist_ok=True)
                
                # 그 안에 날짜 폴더 생성
                folder_name = datetime.now().strftime("%Y.%m.%d")
                target_dir = os.path.join(backup_base_dir, folder_name)
                os.makedirs(target_dir, exist_ok=True)
                
                local_stock_csv = os.path.join(target_dir, "inventory.csv")
                local_history_csv = os.path.join(target_dir, "transactions.csv")
                
                write_csv(local_stock_csv, STOCK_FIELDS, self.stock_rows)
                write_csv(local_history_csv, HISTORY_FIELDS, self.history_rows)
                local_success = True
            except Exception as e:
                QMessageBox.critical(self, "로컬 백업 실패", f"로컬 백업 중 오류가 발생했습니다:\n{str(e)}")
                return
                
        # 2. 이메일 백업 실행
        if modes["email"]:
            cfg = load_email_config()
            if not cfg:
                QMessageBox.warning(self, "이메일 백업 보류", "이메일 백업 설정이 저장되어 있지 않습니다.\n메뉴의 '이메일 백업 설정'을 먼저 진행해 주세요.")
            else:
                try:
                    send_backup_email(cfg)
                    email_success = True
                except Exception as e:
                    QMessageBox.critical(self, "이메일 백업 실패", f"이메일 백업 발송 중 오류가 발생했습니다:\n{str(e)}")
                    
        # 결과 취합 알림
        result_msgs = []
        if local_success:
            result_msgs.append(f"• 로컬 백업 성공 (backup/{folder_name} 폴더 내 생성)")
        if email_success:
            result_msgs.append("• 이메일 백업 메일 발송 성공")
            
        if result_msgs:
            QMessageBox.information(self, "백업 완료", "\n".join(result_msgs))

    def revert_selected_history(self):
        history_row = self.get_selected_history_row()
        if history_row is None:
            QMessageBox.information(self, "안내", "되돌릴 기록을 먼저 선택하세요.")
            return
            
        kind, item_name = history_row.get("구분", ""), history_row.get("자재명", "")
        date_str, qty = history_row.get("일시", ""), history_row.get("수량", "")
        reply = QMessageBox.question(self, "되돌리기 확인", f"구분: {kind}\n품명: {item_name}\n일시: {date_str}\n수량: {qty}\n\n이 기록을 취소하고 원상 복구하시겠습니까?\n이 작업은 되돌릴 수 없습니다.", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes: return
            
        target_index = None
        for i, hrow in enumerate(self.history_rows):
            if hrow.get("일시") == history_row.get("일시") and hrow.get("자재명") == history_row.get("자재명") and hrow.get("구분") == history_row.get("구분") and hrow.get("수량") == history_row.get("수량") and hrow.get("단가") == history_row.get("단가"):
                target_index = i
                break
                
        if target_index is None:
            QMessageBox.warning(self, "오류", "되돌릴 기록을 찾을 수 없습니다.")
            return

        target_record = self.history_rows[target_index]
        hist_qty, hist_kind = to_int(target_record.get("수량", 0)), target_record.get("구분", "")
        
        for item in self.stock_rows:
            if item.get("자재명") == target_record.get("자재명") and item.get("브랜드") == target_record.get("브랜드") and item.get("종류") == target_record.get("종류") and item.get("규격") == target_record.get("규격"):
                current_qty = to_int(item.get("재고", 0))
                if hist_kind == "입고": item["재고"] = str(current_qty - hist_qty)
                elif hist_kind == "출고": item["재고"] = str(current_qty + hist_qty)
                elif hist_kind == "정정":
                    note = target_record.get("비고", "")
                    
                    # 1. 예전 소괄호() 기록 호환성
                    qty_match_old = re.search(r"재고 정정 \(([\d,]+)개 -> ([\d,]+)개\)", note)
                    if qty_match_old: item["재고"] = str(current_qty + (to_int(qty_match_old.group(1)) - to_int(qty_match_old.group(2))))
                    price_match_old = re.search(r"단가 정정 \(([\d,]+)원 -> ([\d,]+)원\)", note)
                    if price_match_old: item["평균단가"] = str(to_int(item.get("평균단가", 0)) + (to_int(price_match_old.group(1)) - to_int(price_match_old.group(2))))
                        
                    # 2. 신규 대괄호[] 방식 적용 및 복구
                    qty_match = re.search(r"재고 정정 \[([\d,]+)개 -> ([\d,]+)개\]", note)
                    if qty_match: item["재고"] = str(current_qty + (to_int(qty_match.group(1)) - to_int(qty_match.group(2))))
                    price_match = re.search(r"단가 정정 \[([\d,]+)원 -> ([\d,]+)원\]", note)
                    if price_match: item["평균단가"] = str(to_int(item.get("평균단가", 0)) + (to_int(price_match.group(1)) - to_int(price_match.group(2))))
                        
                    # 3. 텍스트 변경사항 역산 (예전 글자로 되돌림)
                    text_fields = {
                        "품명": "자재명", "브랜드": "브랜드", "종류": "종류", 
                        "규격": "규격", "단위": "단위", "위치": "위치", "비고": "비고"
                    }
                    for label, key in text_fields.items():
                        match = re.search(rf"{label} 정정 \[(.*?) -> (.*?)\]", note)
                        if match: item[key] = match.group(1)
                break

        del self.history_rows[target_index]
        try:
            write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
            write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
        except Exception as e:
            QMessageBox.critical(self, "데이터 저장 오류", f"데이터 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        self.refresh_all()
        QMessageBox.information(self, "완료", "해당 기록이 취소되고 정보가 정상 복구되었습니다.")

    def open_email_config(self):
        cfg = load_email_config()
        dlg = EmailConfigDialog(self, cfg)
        if not dlg.exec(): return
        new_cfg = dlg.get_cfg()
        if not new_cfg.get("smtp_server") or not new_cfg.get("sender"):
            QMessageBox.warning(self, "확인", "SMTP 서버와 이메일은 필수입니다.")
            return
        save_email_config(new_cfg)
        QMessageBox.information(self, "저장 완료", "이메일 백업 설정이 저장되었습니다.")

    def check_and_send_daily_backup(self):
        if not should_send_backup(): return
        cfg = load_email_config()
        if not cfg: return
        try:
            send_backup_email(cfg)
            record_backup_sent()
            QMessageBox.information(self, "백업 완료", "이메일로 오늘 백업을 보냈습니다.")
        except Exception as e:
            QMessageBox.warning(self, "백업 오류", f"이메일 백업 발송에 실패했습니다.\n{str(e)}")

    def process_inbound_selected(self):
        picker = ItemPickerDialog(self.stock_rows, self, "입고할 품목 선택")
        if not picker.exec(): return
        item_index = picker.selected_index
        if item_index is None: return
        item = self.stock_rows[item_index]
        dlg = InOutDialog("입고 등록", self, item)
        if dlg.exec():
            data = dlg.get_data()
            total_amount = data.get("수량", 0) * data.get("단가", 0)
            if total_amount >= 10000000 or data.get("수량", 0) >= 10000:
                if QMessageBox.warning(self, "이상 수치 감지", f"입력하신 데이터가 너무 큽니다!\n\n수량: {data.get('수량'):,}개\n총 금액: {total_amount:,}원\n\n단위(묶음/낱개)를 혼동하지 않으셨는지 확인해주세요. 이대로 진행하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No:
                    return

            apply_inbound_to_stock(self.stock_rows, self.history_rows, item_index, data)
            try:
                write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
                write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", f"입출고 기록 저장 중 오류가 발생했습니다:\n{str(e)}")
                return
            self.refresh_all()
            QMessageBox.information(self, "완료", "입고 처리되었습니다.")

    def process_outbound_selected(self):
        picker = ItemPickerDialog(self.stock_rows, self, "출고할 품목 선택")
        if not picker.exec(): return
        item_index = picker.selected_index
        if item_index is None: return
        item = self.stock_rows[item_index]
        dlg = InOutDialog("출고 등록", self, item, is_outbound=True)
        dlg.price.setValue(0)
        if dlg.exec():
            data = dlg.get_data()
            total_amount = data.get("수량", 0) * data.get("단가", 0)
            if total_amount >= 10000000 or data.get("수량", 0) >= 10000:
                if QMessageBox.warning(self, "이상 수치 감지", f"입력하신 데이터가 너무 큽니다!\n\n수량: {data.get('수량'):,}개\n총 금액: {total_amount:,}원\n\n단위(묶음/낱개)를 혼동하지 않으셨는지 확인해주세요. 이대로 진행하시겠습니까?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.No:
                    return
            try: apply_outbound_to_stock(self.stock_rows, self.history_rows, item_index, data)
            except ValueError as e:
                QMessageBox.warning(self, "오류", str(e))
                return
            try:
                write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
                write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", f"입출고 기록 저장 중 오류가 발생했습니다:\n{str(e)}")
                return
            self.refresh_all()
            QMessageBox.information(self, "완료", "출고 처리되었습니다.")

    def export_stock_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "재고 CSV 저장", os.path.join(BASE_DIR, "재고목록_백업.csv"), "CSV Files (*.csv)")
        if not path: return
        try:
            write_csv(path, STOCK_FIELDS, self.stock_rows)
            QMessageBox.information(self, "완료", f"저장되었습니다.\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"CSV 저장 중 오류가 발생했습니다:\n{str(e)}")

    def import_stock_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "재고 CSV 불러오기", BASE_DIR, "CSV Files (*.csv)")
        if not path: return
        try: rows = read_csv(path)
        except Exception as e:
            QMessageBox.critical(self, "불러오기 오류", f"CSV 파일을 읽을 수 없습니다:\n{str(e)}")
            return
        if not rows:
            QMessageBox.information(self, "안내", "CSV에 데이터가 없습니다.")
            return
        if "자재명" not in rows[0]:
            QMessageBox.warning(self, "검증 오류", "CSV에 '자재명' 컬럼이 없습니다.\n올바른 재고목록 CSV 파일인지 확인해 주세요.")
            return
        if os.path.exists(STOCK_CSV):
            try: shutil.copy2(STOCK_CSV, os.path.join(BASE_DIR, f"재고목록_백업_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"))
            except Exception: pass
        for row in rows:
            for f in STOCK_FIELDS: row.setdefault(f, "")
        self.stock_rows = rows
        try: write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"CSV 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        try: self.history_rows = read_csv(HISTORY_CSV)
        except Exception: self.history_rows = []
        self.refresh_all()
        QMessageBox.information(self, "완료", "CSV를 불러왔습니다.")

def main():
    app = QApplication(sys.argv)
    window = IMSInventoryApp()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
