#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""공구상가 재고관리 시스템 - Flask 웹앱"""

import csv, json, os, io
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_CSV   = os.path.join(BASE_DIR, "재고목록.csv")
HISTORY_CSV = os.path.join(BASE_DIR, "입출고기록.csv")

STOCK_FIELDS = ["id","브랜드","종류","품명","규격","단위","재고수량","안전재고","평균단가","위치","비고"]
HISTORY_FIELDS = ["번호","일자","구분","브랜드","종류","품명","규격","수량","단가","금액","담당자","비고"]

# ─── CSV 유틸 ───────────────────────────────────────────────

def read_stock():
    if not os.path.exists(STOCK_CSV):
        return []
    with open(STOCK_CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_stock(rows):
    with open(STOCK_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=STOCK_FIELDS)
        w.writeheader()
        w.writerows(rows)

def next_id(rows):
    ids = [int(r.get("id","0")) for r in rows if str(r.get("id","0")).isdigit()]
    return str(max(ids)+1 if ids else 1)

def read_history():
    if not os.path.exists(HISTORY_CSV):
        return []
    with open(HISTORY_CSV, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))

def write_history(rows):
    with open(HISTORY_CSV, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HISTORY_FIELDS)
        w.writeheader()
        w.writerows(rows)

def append_history(row):
    rows = read_history()
    row["번호"] = str(len(rows)+1)
    rows.append(row)
    write_history(rows)

# ─── 라우트 ─────────────────────────────────────────────────

@app.route("/")
def index():
    return redirect(url_for("stock_page"))

@app.route("/stock")
def stock_page():
    return render_template("base.html", active="stock")

@app.route("/inbound")
def inbound_page():
    return render_template("base.html", active="inbound")

@app.route("/outbound")
def outbound_page():
    return render_template("base.html", active="outbound")

@app.route("/history")
def history_page():
    return render_template("base.html", active="history")

@app.route("/manage")
def manage_page():
    return render_template("base.html", active="manage")

# ─── API ────────────────────────────────────────────────────

@app.route("/api/stock")
def api_stock():
    q    = request.args.get("q","").strip().lower()
    page = int(request.args.get("page",1))
    size = int(request.args.get("size",20))
    rows = read_stock()
    if q:
        rows = [r for r in rows if q in r.get("품명","").lower()
                or q in r.get("브랜드","").lower()
                or q in r.get("종류","").lower()]
    total = len(rows)
    start = (page-1)*size
    return jsonify({"total":total,"page":page,"size":size,
                    "pages":(total+size-1)//size if total else 1,
                    "rows":rows[start:start+size]})

@app.route("/api/stock/<sid>")
def api_stock_one(sid):
    rows = read_stock()
    for r in rows:
        if r["id"] == sid:
            return jsonify(r)
    return jsonify({}), 404

@app.route("/api/stock", methods=["POST"])
def api_stock_create():
    data = request.json
    rows = read_stock()
    data["id"] = next_id(rows)
    for f in STOCK_FIELDS:
        data.setdefault(f, "")
    rows.append({f: data.get(f,"") for f in STOCK_FIELDS})
    write_stock(rows)
    return jsonify({"ok":True,"id":data["id"]})

@app.route("/api/stock/<sid>", methods=["PUT"])
def api_stock_update(sid):
    data = request.json
    rows = read_stock()
    for r in rows:
        if r["id"] == sid:
            for f in STOCK_FIELDS:
                if f != "id" and f in data:
                    r[f] = data[f]
    write_stock(rows)
    return jsonify({"ok":True})

@app.route("/api/stock", methods=["DELETE"])
def api_stock_delete():
    ids = request.json.get("ids",[])
    rows = [r for r in read_stock() if r["id"] not in ids]
    write_stock(rows)
    return jsonify({"ok":True})

@app.route("/api/inbound", methods=["POST"])
def api_inbound():
    data = request.json   # {id, 수량, 단가, 담당자, 비고}
    rows = read_stock()
    for r in rows:
        if r["id"] == data["id"]:
            qty_old = float(r.get("재고수량","0") or 0)
            avg_old = float(r.get("평균단가","0") or 0)
            qty_in  = float(data.get("수량","0") or 0)
            price_in= float(data.get("단가","0") or 0)
            qty_new = qty_old + qty_in
            avg_new = ((qty_old*avg_old) + (qty_in*price_in)) / qty_new if qty_new else 0
            r["재고수량"] = str(int(qty_new))
            r["평균단가"]  = str(round(avg_new))
            append_history({
                "번호":"","일자":datetime.now().strftime("%Y-%m-%d %H:%M"),
                "구분":"입고","브랜드":r.get("브랜드",""),"종류":r.get("종류",""),
                "품명":r.get("품명",""),"규격":r.get("규격",""),
                "수량":str(int(qty_in)),"단가":str(int(price_in)),
                "금액":str(int(qty_in*price_in)),
                "담당자":data.get("담당자",""),"비고":data.get("비고","")
            })
            break
    write_stock(rows)
    return jsonify({"ok":True})

@app.route("/api/outbound", methods=["POST"])
def api_outbound():
    data = request.json
    rows = read_stock()
    for r in rows:
        if r["id"] == data["id"]:
            qty_old = float(r.get("재고수량","0") or 0)
            qty_out = float(data.get("수량","0") or 0)
            if qty_out > qty_old:
                return jsonify({"ok":False,"msg":"재고 부족"})
            avg = float(r.get("평균단가","0") or 0)
            r["재고수량"] = str(int(qty_old - qty_out))
            append_history({
                "번호":"","일자":datetime.now().strftime("%Y-%m-%d %H:%M"),
                "구분":"출고","브랜드":r.get("브랜드",""),"종류":r.get("종류",""),
                "품명":r.get("품명",""),"규격":r.get("규격",""),
                "수량":str(int(qty_out)),"단가":str(int(avg)),
                "금액":str(int(qty_out*avg)),
                "담당자":data.get("담당자",""),"비고":data.get("비고","")
            })
            break
    write_stock(rows)
    return jsonify({"ok":True})

@app.route("/api/history")
def api_history():
    q    = request.args.get("q","").strip().lower()
    kind = request.args.get("kind","전체")
    page = int(request.args.get("page",1))
    size = int(request.args.get("size",20))
    rows = read_history()
    if kind != "전체":
        rows = [r for r in rows if r.get("구분") == kind]
    if q:
        rows = [r for r in rows if q in r.get("품명","").lower()
                or q in r.get("브랜드","").lower()]
    rows = list(reversed(rows))
    total = len(rows)
    start = (page-1)*size
    return jsonify({"total":total,"page":page,"size":size,
                    "pages":(total+size-1)//size if total else 1,
                    "rows":rows[start:start+size]})

@app.route("/api/excel/stock")
def excel_stock():
    try:
        import openpyxl
        rows = read_stock()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "재고현황"
        headers = ["No","브랜드","종류","품명","규격","단위","재고수량","단위","평균단가","위치","비고"]
        ws.append(headers)
        for i,r in enumerate(rows,1):
            ws.append([i,r.get("브랜드",""),r.get("종류",""),r.get("품명",""),
                       r.get("규격",""),r.get("단위",""),r.get("재고수량",""),
                       r.get("단위",""),r.get("평균단가",""),r.get("위치",""),r.get("비고","")])
        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)
        return send_file(buf, as_attachment=True,
                         download_name=f"재고현황_{datetime.now().strftime('%Y%m%d')}.xlsx",
                         mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except ImportError:
        return "openpyxl 설치 필요: pip install openpyxl", 500

if __name__ == "__main__":
    # 샘플 데이터 생성
    if not os.path.exists(STOCK_CSV):
        sample = [
            {"id":"1","브랜드":"스탠리","종류":"드라이버","품명":"일자드라이버","규격":"6x150mm","단위":"EA","재고수량":"30","안전재고":"10","평균단가":"3500","위치":"A-01","비고":""},
            {"id":"2","브랜드":"스탠리","종류":"드라이버","품명":"십자드라이버","규격":"6x150mm","단위":"EA","재고수량":"25","안전재고":"10","평균단가":"3800","위치":"A-01","비고":""},
            {"id":"3","브랜드":"보쉬","종류":"드릴","품명":"전동드릴","규격":"12V","단위":"EA","재고수량":"5","안전재고":"2","평균단가":"85000","위치":"B-02","비고":""},
            {"id":"4","브랜드":"보쉬","종류":"드릴","품명":"함마드릴","규격":"18V","단위":"EA","재고수량":"3","안전재고":"1","평균단가":"150000","위치":"B-02","비고":""},
            {"id":"5","브랜드":"밀워키","종류":"렌치","품명":"몽키스패너","규격":"12인치","단위":"EA","재고수량":"15","안전재고":"5","평균단가":"12000","위치":"A-03","비고":""},
            {"id":"6","브랜드":"탑툴","종류":"렌치","품명":"콤비네이션렌치","규격":"10mm","단위":"EA","재고수량":"50","안전재고":"20","평균단가":"3200","위치":"A-04","비고":""},
            {"id":"7","브랜드":"KTC","종류":"소켓","품명":"소켓렌치세트","규격":"1/2인치","단위":"SET","재고수량":"8","안전재고":"3","평균단가":"45000","위치":"C-01","비고":""},
            {"id":"8","브랜드":"대신","종류":"절단","품명":"쇠톱날","규격":"300mm","단위":"EA","재고수량":"100","안전재고":"30","평균단가":"1500","위치":"D-01","비고":""},
            {"id":"9","브랜드":"3M","종류":"소모품","품명":"사포","규격":"#120","단위":"장","재고수량":"200","안전재고":"50","평균단가":"500","위치":"D-02","비고":""},
            {"id":"10","브랜드":"3M","종류":"소모품","품명":"사포","규격":"#240","단위":"장","재고수량":"150","안전재고":"50","평균단가":"500","위치":"D-02","비고":""},
        ]
        write_stock(sample)
    app.run(host="127.0.0.1", port=5050, debug=False)
