#!/Users/mini/.local/bin/python3.11
# -*- coding: utf-8 -*-

import csv
import io
import json
import math
import os
import shutil
import smtplib
import ssl
import sys
import tempfile
import traceback
import zipfile
from datetime import datetime
from typing import List, Dict

from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QColor, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFormLayout, QFrame, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QVBoxLayout, QWidget, QHeaderView, QAbstractItemView, QDialogButtonBox,
    QFileDialog, QListWidget, QSizePolicy
)


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
        self.stock_filter_clear_spacers = {}

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
            clear_btn.setVisible(False)
            clear_btn.clicked.connect(lambda _=False, fn=field_name: self.clear_stock_filter_field(fn))
            clear_spacer = QWidget()
            clear_spacer.setFixedWidth(filter_config["clear_width"])
            clear_spacer.setVisible(True)
            self.stock_filter_buttons[field_name] = button
            self.stock_filter_clear_buttons[field_name] = clear_btn
            self.stock_filter_clear_spacers[field_name] = clear_spacer

            field_row.addWidget(label)
            field_row.addWidget(button)
            field_row.addWidget(clear_btn)
            field_row.addWidget(clear_spacer)
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
        self.table.setHorizontalHeaderLabels([
            "No", "브랜드", "종류", "품명", "규격", "재고", "단위", "평균단가", "위치", "비고"
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
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

    def filtered_items(self):
        return filter_stock_indexed_rows(self.items, self.search.text(), self.stock_filters)

    def refresh_filter_buttons(self):
        for field_name, button in self.stock_filter_buttons.items():
            value = self.stock_filters.get(field_name, "전체")
            button.setText(truncate_filter_label(value))
            button.setToolTip(value if value != "전체" else "")
        for field_name, clear_btn in self.stock_filter_clear_buttons.items():
            is_active = self.stock_filters.get(field_name, "전체") != "전체"
            clear_btn.setVisible(is_active)
            self.stock_filter_clear_spacers[field_name].setVisible(not is_active)
        self.filter_summary_label.setText(active_filter_summary(self.stock_filters))

    def open_stock_filter_picker(self, field_name):
        values = distinct_values(self.items, field_name)
        dlg = ValuePickerDialog(f"{FILTER_FIELD_LABELS[field_name]} 필터 선택", values, self.stock_filters.get(field_name, "전체"), self)
        if not dlg.exec():
            return
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
        widths = [50, 110, 110, 170, 110, 85, 65, 95, 90, 180]
        for i, w in enumerate(widths):
            self.table.setColumnWidth(i, w)

        for row_no, (source_index, row) in enumerate(rows):
            values = [
                str(row_no + 1),
                row.get("브랜드", ""),
                row.get("종류", ""),
                row.get("자재명", ""),
                row.get("규격", ""),
                row.get("재고", "0"),
                row.get("단위", ""),
                f"{to_int(row.get('평균단가', 0)):,}",
                row.get("위치", ""),
                row.get("비고", ""),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, source_index)
                self.table.setItem(row_no, col, item)

        self.table.horizontalHeader().setStretchLastSection(True)

    def select_current(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "안내", "품목을 선택하세요.")
            return
        item = self.table.item(row, 0)
        if not item:
            return
        self.selected_index = item.data(Qt.UserRole)
        self.accept()

def get_base_dir():
    """
    실행 파일의 기준 디렉토리를 반환
    - PyInstaller 빌드: .exe 파일이 있는 폴더 (사용자가 접근 가능한 위치)
    - 개발 환경: 스크립트 파일이 있는 폴더
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller로 빌드된 실행 파일
        return os.path.dirname(sys.executable)
    else:
        # 개발 환경 (Python 스크립트)
        return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = get_base_dir()
STOCK_CSV = os.path.join(BASE_DIR, "inventory.csv")
HISTORY_CSV = os.path.join(BASE_DIR, "transactions.csv")
EMAIL_CONFIG_JSON = os.path.join(BASE_DIR, "email_config.json")
LAST_BACKUP_FILE = os.path.join(BASE_DIR, ".last_backup")

STOCK_FIELDS = [
    "자재명", "브랜드", "종류", "규격", "단위",
    "재고", "평균단가", "사진경로", "비고", "위치"
]

HISTORY_FIELDS = [
    "일시", "구분", "자재명", "브랜드", "종류",
    "규격", "수량", "단가", "금액", "담당자", "비고", "위치"
]

FILTER_FIELD_LABELS = {
    "브랜드": "브랜드",
    "종류": "종류",
    "자재명": "품명",
    "규격": "규격",
    "위치": "위치",
}

INOUT_NEW_ITEM_BUTTON_TEXT = "신규 품목 입고 등록"
NEW_ITEM_INBOUND_DIALOG_TITLE = "신규 품목 입고 등록"
STOCK_PAGE_SIZE = 15
HISTORY_PAGE_SIZE = 15
STOCK_TABLE_VISIBLE_ROWS = 15


def app_stylesheet():
    return """
        QMainWindow { background: #f3f6fa; color: #111827; }
        QDialog { background: #f3f6fa; color: #111827; }
        QLabel { color: #111827; }
        QTabWidget::pane {
            border: 1px solid #cbd5e1;
            background: #ffffff;
            border-radius: 10px;
        }
        QTabBar::tab {
            background: #e5edf9;
            color: #334155;
            padding: 12px 24px;
            margin-right: 4px;
            border: 1px solid #cbd5e1;
            border-bottom: none;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        }
        QTabBar::tab:selected {
            background: #2563eb;
            color: white;
            font-weight: 700;
        }
        QFrame#Card {
            background: #ffffff;
            border: 1px solid #d9e2ec;
            border-radius: 12px;
            padding: 16px;
        }
        QFrame[bottomGroup="true"] {
            background: #edf4ff;
            border: 1px solid #c7d8ee;
            border-radius: 10px;
            padding: 0px;
        }
        QLineEdit, QComboBox, QSpinBox, QTextEdit {
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 8px 10px;
            background: #ffffff;
            color: #111827;
            selection-background-color: #93c5fd;
            selection-color: #0f172a;
            min-height: 18px;
            font-size: 13px;
        }
        QLineEdit::placeholder, QTextEdit[placeholderText="true"] {
            color: #6b7280;
        }
        QPushButton {
            background: #3b82c4;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            font-weight: 600;
        }
        QPushButton[role="secondary"] {
            background: #ffffff;
            color: #334155;
            border: 1px solid #cbd5e1;
        }
        QPushButton[role="secondary"][compact="true"] {
            padding: 6px 10px;
            min-height: 18px;
            font-size: 12px;
        }
        QPushButton[role="filter-clear"] {
            background: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #93c5fd;
            border-radius: 8px;
            padding: 6px 8px;
            min-width: 26px;
            font-weight: 700;
        }
        QPushButton[role="filter-clear"]:hover {
            background: #dbeafe;
            color: #1d4ed8;
        }
        QPushButton[role="secondary"]:hover {
            background: #f8fafc;
            border: 1px solid #94a3b8;
        }
        QPushButton[role="primary-strong"] {
            background: #3b82c4;
            color: white;
            border: 1px solid #2f6fa8;
            font-weight: 800;
            padding: 10px 18px;
        }
        QPushButton:hover { background: #2f6fa8; }
        QPushButton:pressed { background: #285f90; }
        QTableWidget {
            background: #ffffff;
            color: #111827;
            alternate-background-color: #f8fafc;
            gridline-color: #cbd5e1;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-size: 14px;
            selection-background-color: #93c5fd;
            selection-color: #0f172a;
            outline: 0;
        }
        QTableWidget::item {
            padding: 2px;
            border: none;
        }
        QTableWidget::item:selected {
            background: #93c5fd;
            color: #0f172a;
            border: 1px solid #2563eb;
        }
        QTableWidget::item:selected:active {
            background: #93c5fd;
            color: #0f172a;
            border: 1px solid #2563eb;
        }
        QTableWidget::item:selected:!active {
            background: #bfdbfe;
            color: #0f172a;
            border: 1px solid #2563eb;
        }
        QTableWidget[historyTable="true"]::item {
            padding: 4px 6px;
        }
        QHeaderView::section {
            background: #dce6f2;
            color: #1e293b;
            padding: 11px;
            border: none;
            border-right: 1px solid #d2dce8;
            border-bottom: 1px solid #aebfd3;
            font-weight: 800;
            font-size: 13px;
        }
        QListWidget {
            background: #ffffff;
            color: #111827;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            selection-background-color: #93c5fd;
            selection-color: #0f172a;
            outline: 0;
        }
        QListWidget::item:selected {
            background: #93c5fd;
            color: #0f172a;
            border: 1px solid #2563eb;
        }
        QListWidget::item:selected:active {
            background: #93c5fd;
            color: #0f172a;
            border: 1px solid #2563eb;
        }
        QListWidget::item:selected:!active {
            background: #bfdbfe;
            color: #0f172a;
            border: 1px solid #2563eb;
        }
        QMenuBar {
            background: #f3f6fa;
            color: #111827;
            border-bottom: 1px solid #cbd5e1;
        }
        QMenuBar::item:selected {
            background: #dbeafe;
            color: #111827;
        }
        QMenu {
            background: #ffffff;
            color: #111827;
            border: 1px solid #cbd5e1;
        }
        QMenu::item:selected {
            background: #93c5fd;
            color: #0f172a;
        }
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


def ensure_files():
    if not os.path.exists(STOCK_CSV):
        write_csv(STOCK_CSV, STOCK_FIELDS, [])

    if not os.path.exists(HISTORY_CSV):
        write_csv(HISTORY_CSV, HISTORY_FIELDS, [])
    else:
        history = read_csv(HISTORY_CSV)
        changed = False
        for row in history:
            for f in HISTORY_FIELDS:
                if f not in row:
                    row[f] = ""
                    changed = True
        if changed:
            write_csv(HISTORY_CSV, HISTORY_FIELDS, history)

    stock = read_csv(STOCK_CSV)
    changed = False
    for row in stock:
        if "재고" not in row and "현재고" in row:
            row["재고"] = row.get("현재고", "")
            changed = True
        for f in STOCK_FIELDS:
            if f not in row:
                row[f] = ""
                changed = True
    if changed:
        write_csv(STOCK_CSV, STOCK_FIELDS, stock)


def load_email_config():
    if not os.path.exists(EMAIL_CONFIG_JSON):
        return None
    try:
        with open(EMAIL_CONFIG_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def save_email_config(cfg):
    try:
        with open(EMAIL_CONFIG_JSON, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception as e:
        traceback.print_exc()


def should_send_backup():
    if not os.path.exists(LAST_BACKUP_FILE):
        return True
    try:
        with open(LAST_BACKUP_FILE, "r", encoding="utf-8") as f:
            last = f.read().strip()
        today = datetime.now().strftime("%Y-%m-%d")
        return last != today
    except Exception:
        return True


def record_backup_sent():
    try:
        with open(LAST_BACKUP_FILE, "w", encoding="utf-8") as f:
            f.write(datetime.now().strftime("%Y-%m-%d"))
    except Exception:
        pass


def make_backup_zip():
    mem_zip = io.BytesIO()
    with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(STOCK_CSV):
            zf.write(STOCK_CSV, arcname=os.path.basename(STOCK_CSV))
        if os.path.exists(HISTORY_CSV):
            zf.write(HISTORY_CSV, arcname=os.path.basename(HISTORY_CSV))
    mem_zip.seek(0)
    return mem_zip.read(), f"IMS_백업_{datetime.now().strftime('%Y%m%d')}.zip"


def send_backup_email(cfg):
    smtp_server = cfg.get("smtp_server", "")
    smtp_port = cfg.get("smtp_port", 587)
    sender = cfg.get("sender", "")
    password = cfg.get("password", "")
    receiver = cfg.get("receiver", sender)

    if not smtp_server or not sender or not password:
        raise ValueError("이메일 설정이 부족합니다.")

    zip_bytes, zip_name = make_backup_zip()
    today_str = datetime.now().strftime("%Y-%m-%d")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"[IMS 백업] 재고목록 - {today_str}"

    body = (
        f"IMS 재고관리 시스템 자동 백업 메일입니다.\n\n"
        f"발송 일시: {today_str}\n"
        f"첨부파일: {zip_name}\n\n"
        f"본 메일은 발송 전용 주소입니다. 답장을 하지 마세요."
    )
    msg.attach(MIMEText(body, "plain", "utf-8"))

    attachment = MIMEApplication(zip_bytes, name=zip_name)
    attachment.add_header("Content-Disposition", "attachment", filename=zip_name)
    msg.attach(attachment)

    context = ssl.create_default_context()
    if smtp_port == 465:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port, context=context, timeout=30)
    else:
        server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
        server.starttls(context=context)
    server.login(sender, password)
    server.sendmail(sender, receiver, msg.as_string())
    server.quit()
    return True

def read_csv(path: str) -> List[Dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, fieldnames: List[str], rows: List[Dict[str, str]]):
    dir_name = os.path.dirname(os.path.abspath(path)) or "."
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=dir_name,
            suffix=".tmp",
            delete=False,
            encoding="utf-8-sig",
            newline="",
        ) as f:
            tmp_path = f.name
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
        os.replace(tmp_path, path)
    except Exception:
        traceback.print_exc()
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def round_half_up(value):
    """함수_올림(타일2 반올림): 0.5 반디만 할 때 항상 올림기."""
    return math.floor(value + 0.5)


def to_int(value, default=0):
    try:
        return int(str(value).replace(',', '').strip())
    except Exception:
        return default


def distinct_values(rows, field_name):
    values = sorted({str(r.get(field_name, "")).strip() for r in rows if str(r.get(field_name, "")).strip()})
    return values


def filter_option_values(values, query):
    q = str(query or "").strip().lower()
    if not q:
        return values[:]
    return [value for value in values if q in str(value).lower()]


def clear_stock_filter(filters, field_name):
    result = dict(filters or {})
    result[field_name] = "전체"
    return result


def active_filter_summary(filters):
    parts = []
    for field_name in ["브랜드", "종류", "자재명", "규격", "위치"]:
        selected_text = str((filters or {}).get(field_name, "")).strip()
        if selected_text and selected_text != "전체":
            parts.append(f"{FILTER_FIELD_LABELS[field_name]}: {selected_text}")
    return " / ".join(parts) if parts else "적용 필터 없음"


def filter_stock_rows(rows, query, filters=None):
    q = str(query or "").strip().lower()
    active_filters = filters or {}
    result = rows[:]
    if q:
        result = [r for r in result if
                  q in r.get("브랜드", "").lower() or
                  q in r.get("종류", "").lower() or
                  q in r.get("자재명", "").lower() or
                  q in r.get("규격", "").lower() or
                  q in r.get("비고", "").lower() or
                  q in r.get("위치", "").lower()]
    for field_name, selected in active_filters.items():
        selected_text = str(selected or "").strip()
        if selected_text and selected_text != "전체":
            result = [r for r in result if str(r.get(field_name, "")).strip() == selected_text]
    return result


def filter_stock_indexed_rows(rows, query, filters=None):
    q = str(query or "").strip().lower()
    active_filters = filters or {}
    result = []
    for index, row in enumerate(rows):
        if q:
            haystack = " ".join([
                row.get("브랜드", ""), row.get("종류", ""), row.get("자재명", ""),
                row.get("규격", ""), row.get("비고", ""), row.get("위치", "")
            ]).lower()
            if q not in haystack:
                continue
        matched = True
        for field_name, selected in active_filters.items():
            selected_text = str(selected or "").strip()
            if selected_text and selected_text != "전체" and str(row.get(field_name, "")).strip() != selected_text:
                matched = False
                break
        if matched:
            result.append((index, row))
    return result


def build_stock_location_lookup(stock_rows):
    lookup = {}
    for row in stock_rows or []:
        key = stock_identity_key(row)
        location = str(row.get("위치", "")).strip()
        if key not in lookup and location:
            lookup[key] = location
    return lookup


def history_field_value(row, field_name, location_lookup=None):
    if field_name == "위치":
        value = str(row.get("위치", "")).strip()
        if value:
            return value
        return (location_lookup or {}).get(stock_identity_key(row), "")
    return str(row.get(field_name, "")).strip()


def distinct_history_values(rows, field_name, stock_rows=None):
    location_lookup = build_stock_location_lookup(stock_rows)
    values = sorted({
        history_field_value(row, field_name, location_lookup)
        for row in rows
        if history_field_value(row, field_name, location_lookup)
    })
    return values


def filter_history_rows(rows, query, kind, filters=None, stock_rows=None):
    q = str(query or "").strip().lower()
    result = rows[:]
    active_filters = filters or {}
    location_lookup = build_stock_location_lookup(stock_rows)
    if kind and kind != "전체":
        result = [r for r in result if r.get("구분", "") == kind]
    if q:
        result = [r for r in result if
                  q in history_field_value(r, "자재명", location_lookup).lower() or
                  q in history_field_value(r, "브랜드", location_lookup).lower() or
                  q in history_field_value(r, "종류", location_lookup).lower() or
                  q in history_field_value(r, "규격", location_lookup).lower() or
                  q in history_field_value(r, "비고", location_lookup).lower() or
                  q in history_field_value(r, "위치", location_lookup).lower()]
    for field_name, selected in active_filters.items():
        selected_text = str(selected or "").strip()
        if selected_text and selected_text != "전체":
            result = [r for r in result if history_field_value(r, field_name, location_lookup) == selected_text]
    return result


def stock_identity_key(row):
    return (
        str(row.get("자재명", "")).strip(),
        str(row.get("브랜드", "")).strip(),
        str(row.get("종류", "")).strip(),
        str(row.get("규격", "")).strip(),
    )


def is_naturally_linked_inventory(stock_rows, history_rows):
    balances = {}
    for row in sorted(history_rows, key=lambda r: str(r.get("일시", ""))):
        key = stock_identity_key(row)
        kind = str(row.get("구분", "")).strip()
        qty = to_int(row.get("수량"))
        unit_price = to_int(row.get("단가"))
        amount = to_int(row.get("금액"))
        if qty <= 0 or unit_price < 0 or amount != qty * unit_price:
            return False
        current = balances.get(key, 0)
        if kind == "입고":
            balances[key] = current + qty
        elif kind == "출고":
            if qty > current:
                return False
            balances[key] = current - qty
        else:
            return False

    stock_map = {}
    for row in stock_rows:
        key = stock_identity_key(row)
        stock_map[key] = stock_map.get(key, 0) + to_int(row.get("재고"))
    history_keys = set(balances.keys())
    stock_keys = set(stock_map.keys())
    if history_keys != stock_keys:
        return False
    for key, qty in balances.items():
        if stock_map.get(key) != qty:
            return False
    return True


def outbound_shortage_message(item_name, current_qty, request_qty, unit):
    unit_text = unit or ""
    return (
        "재고가 부족합니다.\n\n"
        f"품목: {item_name}\n"
        f"재고: {current_qty}{unit_text}\n"
        f"출고요청: {request_qty}{unit_text}\n\n"
        "출고 수량을 다시 확인해주세요."
    )


def truncate_filter_label(value, max_chars=7):
    """필터 버튼에 표시할 텍스트를 최대 글자수로 잘라 말줄임 처리"""
    if not value or value == "전체":
        return "전체"
    return value if len(value) <= max_chars else value[:max_chars] + "…"


def stock_filter_layout_config():
    return {
        "layout_mode": "row",
        "add_trailing_stretch": True,
        "item_spacing": 88,
        "row_spacing": 16,
        "button_min_width": 93,
        "clear_width": 20,
        "label_width": 28,
        "field_right_margin": 0,
        "card_spacing": 10,
    }


def _filter_field_wrap_width(cfg):
    """필드 한 칸의 고정 너비: 라벨 + spacing + 버튼 + spacing + clear"""
    return cfg["label_width"] + cfg["row_spacing"] + cfg["button_min_width"] + cfg["row_spacing"] + cfg["clear_width"]


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
    if not valid_buttons:
        return 0
    multiplier = max(1, to_int(width_multiplier, 1))
    for button in valid_buttons:
        button.ensurePolished()
    target_width = max(max(button.sizeHint().width(), button.minimumSizeHint().width()) for button in valid_buttons) * multiplier
    for button in valid_buttons:
        button.setFixedWidth(target_width)
    return target_width


def stock_column_widths():
    return [42, 108, 108, 176, 104, 76, 54, 96, 92, 164]


def history_column_widths():
    return [172, 66, 104, 104, 138, 98, 76, 92, 102, 96, 164]


def now_text(now_str=None):
    return now_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stock_total_pages(total_count, page_size):
    safe_page_size = max(1, to_int(page_size, 1))
    return max(1, (max(0, to_int(total_count, 0)) + safe_page_size - 1) // safe_page_size)


def clamp_page_number(page_number, total_pages):
    pages = max(1, to_int(total_pages, 1))
    page = to_int(page_number, 1)
    if page < 1:
        return 1
    if page > pages:
        return pages
    return page


def stock_pagination_summary(current_page, total_pages):
    return f"{clamp_page_number(current_page, total_pages)} / {max(1, to_int(total_pages, 1))} 페이지"


def stock_table_visible_height(row_height=36, visible_rows=STOCK_TABLE_VISIBLE_ROWS, header_height=38, frame_height=12):
    safe_row_height = max(1, to_int(row_height, 36))
    safe_rows = max(1, to_int(visible_rows, STOCK_TABLE_VISIBLE_ROWS))
    return (safe_row_height * safe_rows) + max(0, to_int(header_height, 38)) + max(0, to_int(frame_height, 12))


def history_kind_colors(kind):
    if str(kind or "").strip() == "입고":
        return "#dcfce7", "#111827"
    if str(kind or "").strip() == "출고":
        return "#fee2e2", "#111827"
    return None


def history_kind_badge_stylesheet(kind):
    color_pair = history_kind_colors(kind)
    if not color_pair:
        return "background: transparent; color: #111827; font-weight: 600; padding: 0 6px;"
    bg_color, fg_color = color_pair
    return (
        f"background: {bg_color}; color: {fg_color}; border-radius: 6px; "
        "font-weight: 700; padding: 4px 6px;"
    )


def build_history_kind_badge(kind):
    badge = QLabel(str(kind or ""))
    badge.setAlignment(Qt.AlignCenter)
    badge.setStyleSheet(history_kind_badge_stylesheet(kind))
    return badge


def make_history_row(kind, item, qty, unit_price, staff="", note="", now_str=None):
    return {
        "일시": now_text(now_str),
        "구분": kind,
        "자재명": item.get("자재명", ""),
        "브랜드": item.get("브랜드", ""),
        "종류": item.get("종류", ""),
        "규격": item.get("규격", ""),
        "수량": str(qty),
        "단가": str(unit_price),
        "금액": str(qty * unit_price),
        "담당자": staff,
        "비고": note,
        "위치": item.get("위치", ""),
    }


def apply_inbound_to_stock(stock_rows, history_rows, item_index, inbound_data, now_str=None):
    item = stock_rows[item_index]
    qty_old = to_int(item.get("재고"))
    avg_old = to_int(item.get("평균단가"))
    qty_in = to_int(inbound_data.get("수량"))
    price_in = to_int(inbound_data.get("단가"))
    total_qty = qty_old + qty_in
    new_avg = round_half_up(((qty_old * avg_old) + (qty_in * price_in)) / total_qty) if total_qty else 0
    item["재고"] = str(total_qty)
    item["평균단가"] = str(new_avg)
    history_rows.append(make_history_row(
        "입고", item, qty_in, price_in,
        inbound_data.get("담당자", ""),
        inbound_data.get("비고", ""),
        now_str,
    ))
    return item


def apply_outbound_to_stock(stock_rows, history_rows, item_index, outbound_data, now_str=None):
    item = stock_rows[item_index]
    qty_old = to_int(item.get("재고"))
    qty_out = to_int(outbound_data.get("수량"))
    out_price = to_int(outbound_data.get("단가"))
    if qty_out > qty_old:
        raise ValueError(outbound_shortage_message(
            item.get("자재명", ""),
            qty_old,
            qty_out,
            item.get("단위", "")
        ))
    item["재고"] = str(qty_old - qty_out)
    history_rows.append(make_history_row(
        "출고", item, qty_out, out_price,
        outbound_data.get("담당자", ""),
        outbound_data.get("비고", ""),
        now_str,
    ))
    return item


def create_new_item_inbound(stock_rows, history_rows, item_data, inbound_data, now_str=None):
    new_item = {key: item_data.get(key, "") for key in STOCK_FIELDS}
    new_item["재고"] = "0"
    new_item["평균단가"] = "0"
    new_item.setdefault("사진경로", "")
    stock_rows.append(new_item)
    apply_inbound_to_stock(stock_rows, history_rows, len(stock_rows) - 1, inbound_data, now_str)
    return new_item


class ItemDialog(QDialog):
    def __init__(self, parent=None, data=None):
        super().__init__(parent)
        self.setWindowTitle("자재 등록 / 수정")
        self.setModal(True)
        self.resize(460, 430)

        self.inputs = {}
        self.select_buttons = {}
        self.selectable_fields = ["브랜드", "종류", "자재명", "규격", "단위", "위치"]
        stock_rows = getattr(parent, "stock_rows", []) if parent is not None else []
        self.saved_field_values = {
            field_name: distinct_values(stock_rows, field_name)
            for field_name in self.selectable_fields
        }
        layout = QVBoxLayout(self)
        form = QFormLayout()

        fields = [
            ("브랜드", QLineEdit),
            ("종류", QLineEdit),
            ("자재명", QLineEdit),
            ("규격", QLineEdit),
            ("단위", QLineEdit),
            ("재고", QSpinBox),
            ("평균단가", QSpinBox),
            ("위치", QLineEdit),
            ("비고", QTextEdit),
        ]

        for label, widget_cls in fields:
            widget = widget_cls()
            if isinstance(widget, QSpinBox):
                widget.setRange(0, 999999999)
                widget.setGroupSeparatorShown(True)
            if isinstance(widget, QTextEdit):
                widget.setFixedHeight(80)
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
                self.select_buttons[label] = select_btn
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
                if isinstance(widget, QLineEdit):
                    widget.setText(val)
                elif isinstance(widget, QSpinBox):
                    widget.setValue(to_int(val))
                elif isinstance(widget, QTextEdit):
                    widget.setPlainText(val)

    def open_saved_value_picker(self, field_name):
        values = self.saved_field_values.get(field_name, [])
        if not values:
            QMessageBox.information(self, "안내", f"저장된 {field_name} 값이 없습니다.")
            return
        current = self.inputs[field_name].text().strip() if field_name in self.inputs else ""
        dlg = ValuePickerDialog(f"{field_name} 선택", values, current or "전체", self)
        if not dlg.exec():
            return
        selected = dlg.selected_value or ""
        if selected == "전체":
            selected = ""
        widget = self.inputs.get(field_name)
        if isinstance(widget, QLineEdit):
            widget.setText(selected)

    def get_data(self):
        result = {}
        for key, widget in self.inputs.items():
            if isinstance(widget, QLineEdit):
                result[key] = widget.text().strip()
            elif isinstance(widget, QSpinBox):
                result[key] = str(widget.value())
            elif isinstance(widget, QTextEdit):
                result[key] = widget.toPlainText().strip()
        return result


class InOutDialog(QDialog):
    def __init__(self, title, parent=None, item=None, is_outbound=False):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.resize(380, 260)
        self.item = item or {}

        layout = QVBoxLayout(self)

        lines = [
            f"브랜드: {self.item.get('브랜드','')}",
            f"종류: {self.item.get('종류','')}",
            f"품명: {self.item.get('자재명','')} ({self.item.get('규격','')})",
            f"재고: {self.item.get('재고','0')} {self.item.get('단위','')}"
        ]
        if is_outbound:
            avg = to_int(self.item.get("평균단가", 0))
            if avg > 0:
                lines.append(f"현재 평균원가: {avg:,}원")
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
        return {
            "수량": self.qty.value(),
            "단가": self.price.value(),
            "담당자": self.staff.text().strip(),
            "비고": self.note.text().strip(),
        }


class HistoryEditDialog(QDialog):
    def __init__(self, parent=None, history_row=None):
        super().__init__(parent)
        self.setWindowTitle("입출고 기록 수정")
        self.setModal(True)
        self.resize(440, 440)
        self.history_row = history_row or {}

        layout = QVBoxLayout(self)

        info_wrap = QFrame()
        info_wrap.setObjectName("Card")
        info_layout = QVBoxLayout(info_wrap)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_layout.setSpacing(4)

        info_lines = [
            f"구분: {self.history_row.get('구분', '')}",
            f"브랜드: {self.history_row.get('브랜드', '')}",
            f"품명: {self.history_row.get('자재명', '')} ({self.history_row.get('규격', '')})",
            f"일시: {self.history_row.get('일시', '')}",
        ]
        info_label = QLabel("\n".join(info_lines))
        info_label.setStyleSheet("font-size: 13px; line-height: 1.6; color: #374151;")
        info_layout.addWidget(info_label)
        layout.addWidget(info_wrap)

        form = QFormLayout()
        self.qty = QSpinBox()
        self.qty.setRange(0, 999999999)
        self.qty.setGroupSeparatorShown(True)
        self.qty.setValue(to_int(self.history_row.get("수량", 0)))

        self.price = QSpinBox()
        self.price.setRange(0, 999999999)
        self.price.setGroupSeparatorShown(True)
        self.price.setValue(to_int(self.history_row.get("단가", 0)))

        self.staff = QLineEdit()
        self.staff.setText(self.history_row.get("담당자", ""))

        self.note = QLineEdit()
        self.note.setText(self.history_row.get("비고", ""))

        self.amount_label = QLabel()
        self._update_amount()
        self.qty.valueChanged.connect(self._update_amount)
        self.price.valueChanged.connect(self._update_amount)

        form.addRow("수량", self.qty)
        form.addRow("단가", self.price)
        form.addRow("금액 (계산)", self.amount_label)
        form.addRow("담당자", self.staff)
        form.addRow("비고", self.note)

        layout.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

        input_style = """
            QSpinBox, QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                padding: 8px 10px;
                background: #ffffff;
                color: #111827;
                font-size: 13px;
            }
        """
        self.qty.setStyleSheet(input_style)
        self.price.setStyleSheet(input_style)
        self.staff.setStyleSheet(input_style)
        self.note.setStyleSheet(input_style)
        self.amount_label.setStyleSheet(
            "font-size: 14px; font-weight: 700; color: #2563eb; "
            "padding: 8px; background: #eff6ff; border-radius: 8px;"
        )

    def _update_amount(self):
        qty = self.qty.value()
        price = self.price.value()
        self.amount_label.setText(f"{qty * price:,}원")

    def get_data(self):
        return {
            "수량": self.qty.value(),
            "단가": self.price.value(),
            "담당자": self.staff.text().strip(),
            "비고": self.note.text().strip(),
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
        for value in filtered:
            self.list_widget.addItem(value)
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


EMAIL_PRESETS = {
    "gmail": ("smtp.gmail.com", 587),
    "naver": ("smtp.naver.com", 587),
    "daum": ("smtp.daum.net", 465),
    "custom": ("", 587),
}


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

        if self.cfg:
            self.load_cfg(self.cfg)

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


class IMSInventoryApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMS 재고관리 시스템")
        self.resize(1480, 900)
        self.setMinimumSize(1180, 680)
        self.stock_rows = []
        self.history_rows = []
        self.current_page = 1
        self.page_size = STOCK_PAGE_SIZE
        self.current_history_page = 1
        self.history_page_size = HISTORY_PAGE_SIZE
        self.stock_filter_fields = ["브랜드", "종류", "자재명", "규격", "위치"]
        self.stock_filters = {field_name: "전체" for field_name in self.stock_filter_fields}
        self.stock_filter_buttons = {}
        self.history_filter_fields = ["브랜드", "종류", "자재명", "규격", "위치"]
        self.history_filters = {field_name: "전체" for field_name in self.history_filter_fields}
        self.history_filter_buttons = {}

        # debounce timers
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
        self.stock_filter_clear_buttons = {}
        self.stock_filter_clear_spacers = {}
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
            clear_btn.setVisible(False)
            clear_btn.clicked.connect(lambda _=False, fn=field_name: self.clear_stock_filter_field(fn))
            clear_spacer = QWidget()
            clear_spacer.setFixedWidth(filter_config["clear_width"])
            clear_spacer.setVisible(True)
            self.stock_filter_buttons[field_name] = button
            self.stock_filter_clear_buttons[field_name] = clear_btn
            self.stock_filter_clear_spacers[field_name] = clear_spacer

            field_row.addWidget(label)
            field_row.addWidget(button)
            field_row.addWidget(clear_btn)
            field_row.addWidget(clear_spacer)
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
        self.stock_table.setHorizontalHeaderLabels([
            "No", "브랜드", "종류", "품명", "규격", "재고", "단위", "평균단가", "위치", "비고"
        ])
        self.prepare_table(self.stock_table)
        self.stock_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.stock_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.stock_table.doubleClicked.connect(lambda: self.edit_selected_item())
        self.stock_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.stock_table.setMinimumHeight(0)
        self.stock_table.setMaximumHeight(16777215)
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
        self.history_kind.addItems(["전체", "입고", "출고"])
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
        self.history_filter_clear_buttons = {}
        self.history_filter_clear_spacers = {}
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
            clear_btn.setVisible(False)
            clear_btn.clicked.connect(lambda _=False, fn=field_name: self.clear_history_filter_field(fn))
            clear_spacer = QWidget()
            clear_spacer.setFixedWidth(filter_config["clear_width"])
            clear_spacer.setVisible(True)
            self.history_filter_buttons[field_name] = button
            self.history_filter_clear_buttons[field_name] = clear_btn
            self.history_filter_clear_spacers[field_name] = clear_spacer

            field_row.addWidget(label)
            field_row.addWidget(button)
            field_row.addWidget(clear_btn)
            field_row.addWidget(clear_spacer)
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
        self.history_table.setHorizontalHeaderLabels([
            "일시", "구분", "브랜드", "종류", "품명", "규격", "수량", "단가", "금액", "위치", "비고"
        ])
        self.prepare_table(self.history_table)
        self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.history_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.history_table.setWordWrap(False)
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
        history_edit_btn = QPushButton("변경")
        history_edit_btn.setProperty("role", "primary-strong")
        history_edit_btn.clicked.connect(self.edit_selected_history)
        history_del_btn = QPushButton("삭제")
        history_del_btn.setProperty("role", "secondary")
        history_del_btn.clicked.connect(self.delete_selected_history)
        set_equal_button_widths(history_edit_btn, history_del_btn)
        bottom.addWidget(history_edit_btn)
        bottom.addWidget(history_del_btn)
        layout.addWidget(bottom_row)
        return tab


    def build_menu(self):
        menu = self.menuBar()
        backup_menu = menu.addMenu("백업")
        
        email_cfg_action = QAction("이메일 백업 설정", self)
        email_cfg_action.triggered.connect(self.open_email_config)
        
        backup_menu.addAction(email_cfg_action)

    def apply_styles(self):
        app = QApplication.instance()
        if app:
            app.setPalette(build_fixed_palette())
        self.setStyleSheet(app_stylesheet())

    def prepare_table(self, table: QTableWidget):
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(36)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        table.horizontalHeader().setStretchLastSection(True)
        table.setSelectionMode(QAbstractItemView.SingleSelection)
        table.setShowGrid(True)

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
            is_active = self.stock_filters.get(field_name, "전체") != "전체"
            clear_btn.setVisible(is_active)
            self.stock_filter_clear_spacers[field_name].setVisible(not is_active)
        self.stock_filter_summary_label.setText(active_filter_summary(self.stock_filters))

    def refresh_history_filter_buttons(self):
        for field_name, button in self.history_filter_buttons.items():
            value = self.history_filters.get(field_name, "전체")
            button.setText(truncate_filter_label(value))
            button.setToolTip(value if value != "전체" else "")
        for field_name, clear_btn in self.history_filter_clear_buttons.items():
            is_active = self.history_filters.get(field_name, "전체") != "전체"
            clear_btn.setVisible(is_active)
            self.history_filter_clear_spacers[field_name].setVisible(not is_active)
        self.history_filter_summary_label.setText(active_filter_summary(self.history_filters))

    def reset_stock_search(self):
        self.stock_search.clear()
        self.stock_filters = {field_name: "전체" for field_name in self.stock_filter_fields}
        self.refresh_stock_filter_buttons()
        self.current_page = 1
        self.refresh_stock_table()

    def reset_history_search(self):
        self.history_search.clear()
        self.history_kind.setCurrentText("전체")
        self.history_filters = {field_name: "전체" for field_name in self.history_filter_fields}
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
        if not dlg.exec():
            return
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
        if not dlg.exec():
            return
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
        for i, w in enumerate(widths):
            self.stock_table.setColumnWidth(i, w)

        for i, (source_index, row) in enumerate(page_rows):
            no = start + i + 1
            values = [
                str(no), row.get("브랜드", ""), row.get("종류", ""), row.get("자재명", ""),
                row.get("규격", ""), row.get("재고", "0"), row.get("단위", ""),
                f"{to_int(row.get('평균단가', 0)):,}", row.get("위치", ""), row.get("비고", "")
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setData(Qt.UserRole, source_index)
                if col in (1, 3):
                    item.setForeground(QColor("#2563eb"))
                if col in (5, 7):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif col in (0, 1, 2, 4, 6, 8):
                    item.setTextAlignment(Qt.AlignCenter)
                self.stock_table.setItem(i, col, item)

        self.page_label.setText(stock_pagination_summary(self.current_page, pages))
        self.page_jump_input.setText(str(self.current_page))
        self.stock_count_label.setText(f"등록 품목수: {total}건")

    def refresh_history_table(self):
        rows = filter_history_rows(
            self.history_rows,
            self.history_search.text(),
            self.history_kind.currentText(),
            self.history_filters,
            self.stock_rows,
        )
        rows = list(reversed(rows))
        total = len(rows)
        pages = stock_total_pages(total, self.history_page_size)
        self.current_history_page = clamp_page_number(self.current_history_page, pages)
        start = (self.current_history_page - 1) * self.history_page_size
        page_rows = rows[start:start + self.history_page_size]

        self.history_table.setRowCount(len(page_rows))
        widths = history_column_widths()
        for i, w in enumerate(widths):
            self.history_table.setColumnWidth(i, w)

        location_lookup = build_stock_location_lookup(self.stock_rows)
        for i, row in enumerate(page_rows):
            vals = [
                row.get("일시", ""), row.get("구분", ""), row.get("브랜드", ""), row.get("종류", ""),
                row.get("자재명", ""), row.get("규격", ""), row.get("수량", ""),
                f"{to_int(row.get('단가', 0)):,}", f"{to_int(row.get('금액', 0)):,}",
                history_field_value(row, "위치", location_lookup), row.get("비고", "")
            ]
            for j, val in enumerate(vals):
                item = QTableWidgetItem(val)
                if j == 0:
                    item.setData(Qt.UserRole, row)
                if j == 1:
                    item.setTextAlignment(Qt.AlignCenter)
                    item.setData(Qt.UserRole, row.get("구분", ""))
                elif j in (6, 7, 8):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                elif j in (0, 2, 3, 4, 5, 9):
                    item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(i, j, item)
                if j == 1:
                    self.history_table.setCellWidget(i, j, build_history_kind_badge(row.get("구분", "")))

        self.history_page_label.setText(stock_pagination_summary(self.current_history_page, pages))
        self.history_page_jump_input.setText(str(self.current_history_page))
        self.history_count_label.setText(f"조회 이력수: {total}건")

    def get_selected_index(self):
        row = self.stock_table.currentRow()
        if row < 0:
            return None
        item = self.stock_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def get_selected_item(self):
        index = self.get_selected_index()
        if index is None:
            return None
        if 0 <= index < len(self.stock_rows):
            return self.stock_rows[index]
        return None

    def go_to_page(self, page_number):
        self.current_page = to_int(page_number, 1)
        self.refresh_stock_table()

    def go_to_input_page(self):
        text = self.page_jump_input.text().strip()
        if not text:
            self.page_jump_input.setText(str(self.current_page))
            return
        self.go_to_page(text)

    def prev_page(self):
        self.go_to_page(self.current_page - 1)

    def next_page(self):
        self.go_to_page(self.current_page + 1)

    def go_to_history_page(self, page_number):
        self.current_history_page = to_int(page_number, 1)
        self.refresh_history_table()

    def go_to_input_history_page(self):
        text = self.history_page_jump_input.text().strip()
        if not text:
            self.history_page_jump_input.setText(str(self.current_history_page))
            return
        self.go_to_history_page(text)

    def prev_history_page(self):
        self.go_to_history_page(self.current_history_page - 1)

    def next_history_page(self):
        self.go_to_history_page(self.current_history_page + 1)

    def add_new_item_with_inbound(self):
        item_dlg = ItemDialog(self)
        if not item_dlg.exec():
            return
        item_data = item_dlg.get_data()
        
        # 신규 품목 입고 등록 시 필수 입력 검증
        required_item_fields = {
            "브랜드": "브랜드",
            "종류": "종류",
            "자재명": "품명",
            "단위": "단위",
            "위치": "위치"
        }
        
        missing_fields = []
        for field_key, field_label in required_item_fields.items():
            if not item_data.get(field_key, "").strip():
                missing_fields.append(field_label)
        
        if missing_fields:
            QMessageBox.warning(self, "필수 입력 확인", 
                f"다음 항목을 입력해주세요:\n• {', '.join(missing_fields)}")
            return

        inout_dlg = InOutDialog(NEW_ITEM_INBOUND_DIALOG_TITLE, self, item_data)
        if not inout_dlg.exec():
            return
        inbound_data = inout_dlg.get_data()
        
        # 수량, 단가 필수 검증
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
        dlg = ItemDialog(self, item)
        if dlg.exec():
            new_data = dlg.get_data()
            if not new_data.get("자재명", "").strip():
                QMessageBox.warning(self, "확인", "품명은 필수입니다.")
                return
            item.update(new_data)
            try:
                write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
            except Exception as e:
                QMessageBox.critical(self, "저장 오류", f"재고 목록 저장 중 오류가 발생했습니다:\n{str(e)}")
                return
            self.refresh_all()

    def delete_selected_item(self):
        index = self.get_selected_index()
        if index is None:
            QMessageBox.information(self, "안내", "삭제할 자재를 먼저 선택하세요.")
            return
        item = self.stock_rows[index]
        item_name = item.get("자재명", "")
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"품목: {item_name}\n경고: 이 품목을 삭제하면 되돌릴 수 없습니다.\n정말로 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        del self.stock_rows[index]
        try:
            write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"재고 목록 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        self.current_page = 1
        self.refresh_all()
        QMessageBox.information(self, "완료", "선택한 품목이 삭제되었습니다.")

    def get_selected_history_index(self):
        row = self.history_table.currentRow()
        if row < 0:
            return None
        item = self.history_table.item(row, 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def get_selected_history_row(self):
        item = self.history_table.item(self.history_table.currentRow(), 0)
        if not item:
            return None
        return item.data(Qt.UserRole)

    def edit_selected_history(self):
        history_row = self.get_selected_history_row()
        if history_row is None:
            QMessageBox.information(self, "안내", "수정할 기록을 먼저 선택하세요.")
            return
        dlg = HistoryEditDialog(self, history_row)
        if not dlg.exec():
            return
        data = dlg.get_data()
        if data.get("수량", 0) <= 0:
            QMessageBox.warning(self, "확인", "수량을 1개 이상 입력해주세요.")
            return
        new_qty = data["수량"]
        new_price = data["단가"]
        # UserRole에서 꺼낸 dict가 원본과 동일 객체인지 보장하기 위해
        # 일시+자재명+구분을 key로 원본 self.history_rows에서 찾아 수정
        target = None
        for hrow in self.history_rows:
            if (hrow.get("일시") == history_row.get("일시") and
                    hrow.get("자재명") == history_row.get("자재명") and
                    hrow.get("구분") == history_row.get("구분") and
                    hrow.get("수량") == history_row.get("수량") and
                    hrow.get("단가") == history_row.get("단가")):
                target = hrow
                break
        if target is None:
            QMessageBox.warning(self, "오류", "수정할 기록을 찾을 수 없습니다.")
            return
        target["수량"] = str(new_qty)
        target["단가"] = str(new_price)
        target["금액"] = str(new_qty * new_price)
        target["담당자"] = data["담당자"]
        target["비고"] = data["비고"]
        try:
            write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"기록 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        self.refresh_history_table()
        QMessageBox.information(self, "완료", "입출고 기록이 수정되었습니다.")

    def delete_selected_history(self):
        history_row = self.get_selected_history_row()
        if history_row is None:
            QMessageBox.information(self, "안내", "삭제할 기록을 먼저 선택하세요.")
            return
        kind = history_row.get("구분", "")
        item_name = history_row.get("자재명", "")
        date_str = history_row.get("일시", "")
        qty = history_row.get("수량", "")
        reply = QMessageBox.question(
            self, "삭제 확인",
            f"구분: {kind}\n품명: {item_name}\n일시: {date_str}\n수량: {qty}\n\n"
            f"이 기록을 삭제하면 되돌릴 수 없습니다.\n정말 삭제하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        target_index = None
        for i, hrow in enumerate(self.history_rows):
            if (hrow.get("일시") == history_row.get("일시") and
                    hrow.get("자재명") == history_row.get("자재명") and
                    hrow.get("구분") == history_row.get("구분") and
                    hrow.get("수량") == history_row.get("수량") and
                    hrow.get("단가") == history_row.get("단가")):
                target_index = i
                break
        if target_index is None:
            QMessageBox.warning(self, "오류", "삭제할 기록을 찾을 수 없습니다.")
            return
        del self.history_rows[target_index]
        try:
            write_csv(HISTORY_CSV, HISTORY_FIELDS, self.history_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"기록 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        self.refresh_history_table()
        QMessageBox.information(self, "완료", "입출고 기록이 삭제되었습니다.")

    def open_email_config(self):
        cfg = load_email_config()
        dlg = EmailConfigDialog(self, cfg)
        if not dlg.exec():
            return
        new_cfg = dlg.get_cfg()
        if not new_cfg.get("smtp_server") or not new_cfg.get("sender"):
            QMessageBox.warning(self, "확인", "SMTP 서버와 이메일은 필수입니다.")
            return
        save_email_config(new_cfg)
        QMessageBox.information(self, "저장 완료", "이메일 백업 설정이 저장되었습니다.")

    def check_and_send_daily_backup(self):
        if not should_send_backup():
            return
        cfg = load_email_config()
        if not cfg:
            return
        try:
            send_backup_email(cfg)
            record_backup_sent()
            QMessageBox.information(self, "백업 완료", "이메일로 오늘 백업을 보냈습니다.")
        except Exception as e:
            QMessageBox.warning(self, "백업 오류", f"이메일 백업 발송에 실패했습니다.\n{str(e)}")

    def process_inbound_selected(self):
        picker = ItemPickerDialog(self.stock_rows, self, "입고할 품목 선택")
        if not picker.exec():
            return
        item_index = picker.selected_index
        if item_index is None:
            return
        item = self.stock_rows[item_index]
        dlg = InOutDialog("입고 등록", self, item)
        if dlg.exec():
            data = dlg.get_data()
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
        if not picker.exec():
            return
        item_index = picker.selected_index
        if item_index is None:
            return
        item = self.stock_rows[item_index]
        dlg = InOutDialog("출고 등록", self, item, is_outbound=True)
        dlg.price.setValue(0)
        if dlg.exec():
            data = dlg.get_data()
            try:
                apply_outbound_to_stock(self.stock_rows, self.history_rows, item_index, data)
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
        if not path:
            return
        try:
            write_csv(path, STOCK_FIELDS, self.stock_rows)
            QMessageBox.information(self, "완료", f"저장되었습니다.\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"CSV 저장 중 오류가 발생했습니다:\n{str(e)}")

    def import_stock_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "재고 CSV 불러오기", BASE_DIR, "CSV Files (*.csv)")
        if not path:
            return
        try:
            rows = read_csv(path)
        except Exception as e:
            QMessageBox.critical(self, "불러오기 오류", f"CSV 파일을 읽을 수 없습니다:\n{str(e)}")
            return
        if not rows:
            QMessageBox.information(self, "안내", "CSV에 데이터가 없습니다.")
            return
        first = rows[0]
        if "자재명" not in first:
            QMessageBox.warning(self, "검증 오류", "CSV에 '자재명' 컬럼이 없습니다.\n올바른 재고목록 CSV 파일인지 확인해 주세요.")
            return
        # 백업
        if os.path.exists(STOCK_CSV):
            backup_path = os.path.join(BASE_DIR, f"재고목록_백업_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            try:
                shutil.copy2(STOCK_CSV, backup_path)
            except Exception:
                pass
        for row in rows:
            for f in STOCK_FIELDS:
                row.setdefault(f, "")
        self.stock_rows = rows
        try:
            write_csv(STOCK_CSV, STOCK_FIELDS, self.stock_rows)
        except Exception as e:
            QMessageBox.critical(self, "저장 오류", f"CSV 저장 중 오류가 발생했습니다:\n{str(e)}")
            return
        try:
            self.history_rows = read_csv(HISTORY_CSV)
        except Exception:
            self.history_rows = []
        self.refresh_all()
        QMessageBox.information(self, "완료", "CSV를 불러왔습니다.")


def main():
    app = QApplication(sys.argv)
    window = IMSInventoryApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
