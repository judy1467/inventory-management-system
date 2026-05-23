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
import re
from datetime import datetime
from typing import List, Dict
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()
STOCK_CSV = os.path.join(BASE_DIR, "inventory.csv")
HISTORY_CSV = os.path.join(BASE_DIR, "transactions.csv")
EMAIL_CONFIG_JSON = os.path.join(BASE_DIR, "email_config.json")
LAST_BACKUP_FILE = os.path.join(BASE_DIR, ".last_backup")

STOCK_FIELDS = ["자재명", "브랜드", "종류", "규격", "단위", "재고", "평균단가", "사진경로", "비고", "위치"]
HISTORY_FIELDS = ["일시", "구분", "자재명", "브랜드", "종류", "규격", "수량", "단가", "금액", "담당자", "비고", "위치"]
FILTER_FIELD_LABELS = {"브랜드": "브랜드", "종류": "종류", "자재명": "품명", "규격": "규격", "위치": "위치"}

INOUT_NEW_ITEM_BUTTON_TEXT = "신규 품목 입고 등록"
NEW_ITEM_INBOUND_DIALOG_TITLE = "신규 품목 입고 등록"
STOCK_PAGE_SIZE = 15
HISTORY_PAGE_SIZE = 15
STOCK_TABLE_VISIBLE_ROWS = 15

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
    if not os.path.exists(EMAIL_CONFIG_JSON): return None
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
    if not os.path.exists(LAST_BACKUP_FILE): return True
    try:
        with open(LAST_BACKUP_FILE, "r", encoding="utf-8") as f:
            last = f.read().strip()
        return last != datetime.now().strftime("%Y-%m-%d")
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
    smtp_server, smtp_port = cfg.get("smtp_server", ""), cfg.get("smtp_port", 587)
    sender, password = cfg.get("sender", ""), cfg.get("password", "")
    receiver = cfg.get("receiver", sender)

    if not smtp_server or not sender or not password:
        raise ValueError("이메일 설정이 부족합니다.")

    zip_bytes, zip_name = make_backup_zip()
    today_str = datetime.now().strftime("%Y-%m-%d")

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = receiver
    msg["Subject"] = f"[IMS 백업] 재고목록 - {today_str}"
    body = f"IMS 재고관리 시스템 자동 백업 메일입니다.\n\n발송 일시: {today_str}\n첨부파일: {zip_name}\n\n본 메일은 발송 전용 주소입니다. 답장을 하지 마세요."
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
    if not os.path.exists(path): return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def write_csv(path: str, fieldnames: List[str], rows: List[Dict[str, str]]):
    dir_name = os.path.dirname(os.path.abspath(path)) or "."
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", dir=dir_name, suffix=".tmp", delete=False, encoding="utf-8-sig", newline="") as f:
            tmp_path = f.name
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for row in rows:
                writer.writerow({key: row.get(key, "") for key in fieldnames})
        os.replace(tmp_path, path)
    except Exception:
        traceback.print_exc()
        if tmp_path and os.path.exists(tmp_path): os.remove(tmp_path)
        raise

def round_half_up(value): return math.floor(value + 0.5)

def to_int(value, default=0):
    if value is None: return default
    # 숫자와 마이너스(-) 기호만 남기고 모두 제거
    clean_val = re.sub(r'[^0-9-]', '', str(value))
    try:
        return int(clean_val)
    except ValueError:
        return default

def distinct_values(rows, field_name):
    return sorted({str(r.get(field_name, "")).strip() for r in rows if str(r.get(field_name, "")).strip()})

def filter_option_values(values, query):
    q = str(query or "").strip().lower()
    if not q: return values[:]
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
        result = [r for r in result if q in r.get("브랜드", "").lower() or q in r.get("종류", "").lower() or q in r.get("자재명", "").lower() or q in r.get("규격", "").lower() or q in r.get("비고", "").lower() or q in r.get("위치", "").lower()]
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
            haystack = " ".join([row.get("브랜드", ""), row.get("종류", ""), row.get("자재명", ""), row.get("규격", ""), row.get("비고", ""), row.get("위치", "")]).lower()
            if q not in haystack: continue
        matched = True
        for field_name, selected in active_filters.items():
            selected_text = str(selected or "").strip()
            if selected_text and selected_text != "전체" and str(row.get(field_name, "")).strip() != selected_text:
                matched = False
                break
        if matched: result.append((index, row))
    return result

def build_stock_location_lookup(stock_rows):
    lookup = {}
    for row in stock_rows or []:
        key = stock_identity_key(row)
        location = str(row.get("위치", "")).strip()
        if key not in lookup and location: lookup[key] = location
    return lookup

def history_field_value(row, field_name, location_lookup=None):
    if field_name == "위치":
        value = str(row.get("위치", "")).strip()
        if value: return value
        return (location_lookup or {}).get(stock_identity_key(row), "")
    return str(row.get(field_name, "")).strip()

def distinct_history_values(rows, field_name, stock_rows=None):
    location_lookup = build_stock_location_lookup(stock_rows)
    return sorted({history_field_value(row, field_name, location_lookup) for row in rows if history_field_value(row, field_name, location_lookup)})

def filter_history_rows(rows, query, kind, filters=None, stock_rows=None):
    q = str(query or "").strip().lower()
    result = rows[:]
    active_filters = filters or {}
    location_lookup = build_stock_location_lookup(stock_rows)
    if kind and kind != "전체": result = [r for r in result if r.get("구분", "") == kind]
    if q:
        result = [r for r in result if q in history_field_value(r, "자재명", location_lookup).lower() or q in history_field_value(r, "브랜드", location_lookup).lower() or q in history_field_value(r, "종류", location_lookup).lower() or q in history_field_value(r, "규격", location_lookup).lower() or q in history_field_value(r, "비고", location_lookup).lower() or q in history_field_value(r, "위치", location_lookup).lower()]
    for field_name, selected in active_filters.items():
        selected_text = str(selected or "").strip()
        if selected_text and selected_text != "전체":
            result = [r for r in result if history_field_value(r, field_name, location_lookup) == selected_text]
    return result

def stock_identity_key(row):
    return (str(row.get("자재명", "")).strip(), str(row.get("브랜드", "")).strip(), str(row.get("종류", "")).strip(), str(row.get("규격", "")).strip())

def is_naturally_linked_inventory(stock_rows, history_rows):
    balances = {}
    for row in sorted(history_rows, key=lambda r: str(r.get("일시", ""))):
        key = stock_identity_key(row)
        kind = str(row.get("구분", "")).strip()
        qty, unit_price, amount = to_int(row.get("수량")), to_int(row.get("단가")), to_int(row.get("금액"))
        if qty <= 0 or unit_price < 0 or amount != qty * unit_price: return False
        current = balances.get(key, 0)
        if kind == "입고": balances[key] = current + qty
        elif kind == "출고":
            if qty > current: return False
            balances[key] = current - qty
        else: return False

    stock_map = {}
    for row in stock_rows:
        key = stock_identity_key(row)
        stock_map[key] = stock_map.get(key, 0) + to_int(row.get("재고"))
    if set(balances.keys()) != set(stock_map.keys()): return False
    for key, qty in balances.items():
        if stock_map.get(key) != qty: return False
    return True

def outbound_shortage_message(item_name, current_qty, request_qty, unit):
    unit_text = unit or ""
    return f"재고가 부족합니다.\n\n품목: {item_name}\n재고: {current_qty}{unit_text}\n출고요청: {request_qty}{unit_text}\n\n출고 수량을 다시 확인해주세요."

def truncate_filter_label(value, max_chars=7):
    if not value or value == "전체": return "전체"
    return value if len(value) <= max_chars else value[:max_chars] + "…"

def now_text(now_str=None): return now_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def stock_total_pages(total_count, page_size):
    safe_page_size = max(1, to_int(page_size, 1))
    return max(1, (max(0, to_int(total_count, 0)) + safe_page_size - 1) // safe_page_size)

def clamp_page_number(page_number, total_pages):
    pages = max(1, to_int(total_pages, 1))
    page = to_int(page_number, 1)
    if page < 1: return 1
    if page > pages: return pages
    return page

def stock_pagination_summary(current_page, total_pages):
    return f"{clamp_page_number(current_page, total_pages)} / {max(1, to_int(total_pages, 1))} 페이지"

def make_history_row(kind, item, qty, unit_price, staff="", note="", now_str=None):
    return {
        "일시": now_text(now_str), "구분": kind, "자재명": item.get("자재명", ""), "브랜드": item.get("브랜드", ""),
        "종류": item.get("종류", ""), "규격": item.get("규격", ""), "수량": str(qty), "단가": str(unit_price),
        "금액": str(qty * unit_price), "담당자": staff, "비고": note, "위치": item.get("위치", ""),
    }

def apply_inbound_to_stock(stock_rows, history_rows, item_index, inbound_data, now_str=None):
    item = stock_rows[item_index]
    qty_old, avg_old = to_int(item.get("재고")), to_int(item.get("평균단가"))
    qty_in, price_in = to_int(inbound_data.get("수량")), to_int(inbound_data.get("단가"))
    total_qty = qty_old + qty_in
    new_avg = round_half_up(((qty_old * avg_old) + (qty_in * price_in)) / total_qty) if total_qty else 0
    item["재고"], item["평균단가"] = str(total_qty), str(new_avg)
    history_rows.append(make_history_row("입고", item, qty_in, price_in, inbound_data.get("담당자", ""), inbound_data.get("비고", ""), now_str))
    return item

def apply_outbound_to_stock(stock_rows, history_rows, item_index, outbound_data, now_str=None):
    item = stock_rows[item_index]
    qty_old = to_int(item.get("재고"))
    qty_out, out_price = to_int(outbound_data.get("수량")), to_int(outbound_data.get("단가"))
    if qty_out > qty_old: raise ValueError(outbound_shortage_message(item.get("자재명", ""), qty_old, qty_out, item.get("단위", "")))
    item["재고"] = str(qty_old - qty_out)
    history_rows.append(make_history_row("출고", item, qty_out, out_price, outbound_data.get("담당자", ""), outbound_data.get("비고", ""), now_str))
    return item

def apply_correction_to_history(history_rows, old_data, new_data, now_str=None):
    old_qty, new_qty = to_int(old_data.get("재고", 0)), to_int(new_data.get("재고", 0))
    old_price, new_price = to_int(old_data.get("평균단가", 0)), to_int(new_data.get("평균단가", 0))
    
    qty_diff = new_qty - old_qty
    notes = []
    
    if qty_diff != 0: 
        notes.append(f"재고 정정 [{old_qty}개 -> {new_qty}개]")
    if old_price != new_price: 
        notes.append(f"단가 정정 [{old_price:,}원 -> {new_price:,}원]")
        
    # 텍스트 항목 변경 감지
    text_fields = {
        "자재명": "품명", "브랜드": "브랜드", "종류": "종류", 
        "규격": "규격", "단위": "단위", "위치": "위치", "비고": "비고"
    }
    
    for key, label in text_fields.items():
        o_val = str(old_data.get(key, "")).strip()
        n_val = str(new_data.get(key, "")).strip()
        if o_val != n_val:
            notes.append(f"{label} 정정 [{o_val} -> {n_val}]")
            
    if not notes:
        return  # 변경된 내용이 없으면 기록하지 않음
        
    note_text = " | ".join(notes)
    
    history_rows.append({
        "일시": now_text(now_str), 
        "구분": "정정", 
        "자재명": new_data.get("자재명", ""), 
        "브랜드": new_data.get("브랜드", ""),
        "종류": new_data.get("종류", ""), 
        "규격": new_data.get("규격", ""), 
        "수량": str(abs(qty_diff)) if qty_diff != 0 else "0",
        "단가": str(new_price), 
        "금액": f"{abs(qty_diff) * new_price:,}" if qty_diff != 0 else "0",
        "담당자": "시스템관리자", 
        "비고": note_text, 
        "위치": new_data.get("위치", "")
    })

def create_new_item_inbound(stock_rows, history_rows, item_data, inbound_data, now_str=None):
    new_item = {key: item_data.get(key, "") for key in STOCK_FIELDS}
    new_item["재고"], new_item["평균단가"] = "0", "0"
    new_item.setdefault("사진경로", "")
    stock_rows.append(new_item)
    apply_inbound_to_stock(stock_rows, history_rows, len(stock_rows) - 1, inbound_data, now_str)
    return new_item
