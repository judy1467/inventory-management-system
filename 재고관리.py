#!/Users/mini/.local/bin/python3.11
# -*- coding: utf-8 -*-
"""
공구상가 자재 재고관리 프로그램 v2
- 이동평균법 단가 계산
- 재고현황: No / 사진 / 브랜드 / 종류 / 품명(규격) / 재고수량 / 단위 / 평균단가
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import csv
import os
from datetime import datetime
from PIL import Image, ImageTk   # pip install pillow (없으면 사진 미표시)

# ── 파일 경로 ────────────────────────────────────────────────────
BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
ITEMS_FILE   = os.path.join(BASE_DIR, "재고목록.csv")
HISTORY_FILE = os.path.join(BASE_DIR, "입출고기록.csv")

ITEMS_HEADER = [
    "자재코드","자재명","브랜드","종류","규격",
    "단위","현재고","안전재고","평균단가","사진경로","비고"
]
HISTORY_HEADER = [
    "일시","종류","자재코드","자재명","수량","단가","합계금액","담당자","비고"
]

# ── 테마 ────────────────────────────────────────────────────────
BG     = "#1e1e2e"
PANEL  = "#2a2a3d"
ACCENT = "#89b4fa"
GREEN  = "#a6e3a1"
RED    = "#f38ba8"
YELLOW = "#f9e2af"
FG     = "#cdd6f4"
MUTED  = "#6c7086"
BTN_BG = "#313244"

THUMB_SIZE = (40, 40)   # 재고현황 사진 썸네일 크기

# ── CSV 유틸 ────────────────────────────────────────────────────
def load_csv(path, header):
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerow(header)
        return []
    with open(path, encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    # 구버전 파일 호환: 없는 컬럼은 빈값으로 채움
    for row in rows:
        for col in header:
            row.setdefault(col, "")
    return rows

def save_csv(path, header, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

# ── 이동평균 계산 ────────────────────────────────────────────────
def calc_moving_avg(cur_stock, cur_avg, in_qty, in_price):
    """입고 시 이동평균단가 재계산"""
    total_qty   = cur_stock + in_qty
    if total_qty == 0:
        return in_price
    total_value = cur_stock * cur_avg + in_qty * in_price
    return round(total_value / total_qty, 2)

# ── 썸네일 로더 ──────────────────────────────────────────────────
_thumb_cache = {}   # path → PhotoImage (GC 방지)

def load_thumb(path):
    if not path or not os.path.exists(path):
        return None
    if path in _thumb_cache:
        return _thumb_cache[path]
    try:
        img = Image.open(path).convert("RGBA")
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        # 정사각형 패딩
        bg = Image.new("RGBA", THUMB_SIZE, (42, 42, 61, 255))
        off = ((THUMB_SIZE[0]-img.width)//2, (THUMB_SIZE[1]-img.height)//2)
        bg.paste(img, off, img)
        tk_img = ImageTk.PhotoImage(bg)
        _thumb_cache[path] = tk_img
        return tk_img
    except Exception:
        return None

# ════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🔧 공구상가 자재 재고관리")
        self.geometry("1340x800")
        self.minsize(1000, 600)
        self.configure(bg=BG)

        self.items   = load_csv(ITEMS_FILE,   ITEMS_HEADER)
        self.history = load_csv(HISTORY_FILE, HISTORY_HEADER)

        self._apply_style()
        self._build_ui()
        self._refresh_inventory()

    # ── 스타일 ──────────────────────────────────────────────────
    def _apply_style(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",        background=BG,    borderwidth=0)
        s.configure("TNotebook.Tab",    background=BTN_BG, foreground=FG,
                    padding=[18,8],     font=("맑은 고딕",10))
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG)])
        s.configure("Treeview",         background=PANEL, fieldbackground=PANEL,
                    foreground=FG,      rowheight=46,      font=("맑은 고딕",9))
        s.configure("Treeview.Heading", background=BTN_BG, foreground=ACCENT,
                    font=("맑은 고딕",9,"bold"))
        s.map("Treeview",
              background=[("selected", ACCENT)],
              foreground=[("selected", BG)])
        s.configure("TCombobox",        fieldbackground=PANEL, background=BTN_BG,
                    foreground=FG,      font=("맑은 고딕",10))
        s.configure("TEntry",           fieldbackground=PANEL, foreground=FG,
                    font=("맑은 고딕",10))

    # ── UI 뼈대 ─────────────────────────────────────────────────
    def _build_ui(self):
        title_bar = tk.Frame(self, bg=PANEL, height=56)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)
        tk.Label(title_bar, text="🔧 공구상가 자재 재고관리",
                 font=("맑은 고딕",16,"bold"), bg=PANEL, fg=ACCENT
                 ).pack(side="left", padx=20, pady=10)
        self._clock = tk.StringVar()
        tk.Label(title_bar, textvariable=self._clock,
                 font=("맑은 고딕",10), bg=PANEL, fg=MUTED
                 ).pack(side="right", padx=20)
        self._tick()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=12, pady=8)

        self.f_inv  = tk.Frame(nb, bg=BG)
        self.f_in   = tk.Frame(nb, bg=BG)
        self.f_out  = tk.Frame(nb, bg=BG)
        self.f_hist = tk.Frame(nb, bg=BG)
        self.f_item = tk.Frame(nb, bg=BG)

        nb.add(self.f_inv,  text="  📦 재고현황  ")
        nb.add(self.f_in,   text="  ⬇️ 입고등록  ")
        nb.add(self.f_out,  text="  ⬆️ 출고등록  ")
        nb.add(self.f_hist, text="  📋 입출고기록  ")
        nb.add(self.f_item, text="  ⚙️ 자재관리  ")

        self._build_tab_inv()
        self._build_tab_inout(self.f_in,  "입고", GREEN)
        self._build_tab_inout(self.f_out, "출고", RED)
        self._build_tab_hist()
        self._build_tab_item()

    def _tick(self):
        self._clock.set(datetime.now().strftime("%Y-%m-%d  %H:%M:%S"))
        self.after(1000, self._tick)

    # ── 공용 헬퍼 ───────────────────────────────────────────────
    def _label(self, parent, text, fg=MUTED, font=("맑은 고딕",9)):
        return tk.Label(parent, text=text, bg=BG, fg=fg, font=font)

    def _entry(self, parent, textvariable, width=18):
        return ttk.Entry(parent, textvariable=textvariable, width=width)

    def _btn(self, parent, text, cmd, bg=BTN_BG, fg=FG, w=12):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         font=("맑은 고딕",9), width=w, relief="flat",
                         activebackground=ACCENT, activeforeground=BG, cursor="hand2")

    # ══════════════════════════════════════════════════════════
    # 탭 1 – 재고현황
    # 컬럼: No. / 사진 / 브랜드 / 종류 / 품명(규격) / 재고수량 / 단위 / 평균단가
    # ══════════════════════════════════════════════════════════
    def _build_tab_inv(self):
        top = tk.Frame(self.f_inv, bg=BG)
        top.pack(fill="x", padx=12, pady=8)

        self._label(top, "검색:").pack(side="left")
        self._sv_search = tk.StringVar()
        self._sv_search.trace_add("write", lambda *_: self._refresh_inventory())
        self._entry(top, self._sv_search, 24).pack(side="left", padx=6)
        self._btn(top, "🔄 새로고침", self._refresh_inventory, w=12).pack(side="left", padx=4)

        cols = ["No.","사진","브랜드","종류","품명(규격)","재고수량","단위","평균단가"]
        widths = [45, 50, 110, 110, 200, 80, 60, 100]
        anchors = ["center","center","center","center","w","center","center","e"]

        self.tree_inv = ttk.Treeview(self.f_inv, columns=cols, show="headings")
        for c, w, a in zip(cols, widths, anchors):
            self.tree_inv.heading(c, text=c)
            self.tree_inv.column(c, width=w, anchor=a, minwidth=w)

        sb = ttk.Scrollbar(self.f_inv, orient="vertical", command=self.tree_inv.yview)
        self.tree_inv.configure(yscrollcommand=sb.set)
        self.tree_inv.pack(fill="both", expand=True, padx=(12,0), pady=(0,4), side="left")
        sb.pack(side="right", fill="y", pady=(0,4), padx=(0,4))

        # 이미지 참조 보관 (GC 방지)
        self._inv_images = {}

    def _refresh_inventory(self):
        kw = self._sv_search.get().lower()
        for r in self.tree_inv.get_children():
            self.tree_inv.delete(r)
        self._inv_images.clear()

        for idx, it in enumerate(self.items, 1):
            name = it.get("자재명", "")
            spec = it.get("규격", "")
            brand = it.get("브랜드", "")
            kind  = it.get("종류", "")
            # 검색 필터
            search_str = f"{it.get('자재코드','')} {name} {brand} {kind} {spec}".lower()
            if kw and kw not in search_str:
                continue

            try:
                stock = int(it.get("현재고", 0))
            except ValueError:
                stock = 0
            try:
                avg_price = float(it.get("평균단가", 0))
            except ValueError:
                avg_price = 0.0

            # 품명(규격) 합치기
            품명규격 = f"{name}  [{spec}]" if spec else name

            # 평균단가 표시 (소수점 있으면 표시)
            if avg_price == int(avg_price):
                price_str = f"{int(avg_price):,} 원"
            else:
                price_str = f"{avg_price:,.1f} 원"

            # 사진 썸네일
            photo_path = it.get("사진경로", "")
            thumb = load_thumb(photo_path)
            iid = it["자재코드"]

            if thumb:
                self._inv_images[iid] = thumb
                self.tree_inv.insert("", "end", iid=iid,
                    image=thumb,   # treeview는 첫 열 이미지만 지원 → 사진 컬럼에 빈값, 이미지는 행에
                    values=(idx, "", brand, kind, 품명규격, stock, it.get("단위",""), price_str))
                # 사진 컬럼에 실제 이미지 넣기 (tag image trick)
                self.tree_inv.item(iid, image=thumb)
            else:
                self.tree_inv.insert("", "end", iid=iid,
                    values=(idx, "📷", brand, kind, 품명규격, stock, it.get("단위",""), price_str))

    # ══════════════════════════════════════════════════════════
    # 탭 2,3 – 입고/출고 등록
    # ══════════════════════════════════════════════════════════
    def _build_tab_inout(self, frame, kind, color):
        icon = "⬇️" if kind == "입고" else "⬆️"
        tk.Label(frame, text=f"{icon} {kind} 등록",
                 font=("맑은 고딕",13,"bold"), bg=BG, fg=color
                 ).pack(pady=(16,4))

        form = tk.Frame(frame, bg=BG)
        form.pack(pady=8)

        sv_code  = tk.StringVar()
        sv_name  = tk.StringVar()
        sv_brand = tk.StringVar()
        sv_kind2 = tk.StringVar()
        sv_spec  = tk.StringVar()
        sv_unit  = tk.StringVar()
        sv_avg   = tk.StringVar()   # 현재 이동평균단가 (표시용)
        sv_price = tk.StringVar()   # 이번 입고/출고 단가
        sv_stock = tk.StringVar()   # 현재 재고 (표시용)
        sv_qty   = tk.StringVar()
        sv_who   = tk.StringVar()
        sv_note  = tk.StringVar()

        labels = ["자재코드", "자재명", "브랜드", "종류", "규격",
                  "단위", "현재고", "현재 평균단가", "이번 단가(원)", "수량", "담당자", "비고"]
        svars  = [sv_code, sv_name, sv_brand, sv_kind2, sv_spec,
                  sv_unit, sv_stock, sv_avg, sv_price, sv_qty, sv_who, sv_note]
        editable = [False, False, False, False, False,
                    False, False, False, True, True, True, True]

        for i, (lbl, sv, ed) in enumerate(zip(labels, svars, editable)):
            tk.Label(form, text=lbl, bg=BG, fg=MUTED,
                     font=("맑은 고딕",10), anchor="e", width=14
                     ).grid(row=i, column=0, padx=(20,4), pady=5, sticky="e")
            if i == 0:
                # 자재코드 → 콤보박스
                codes = [f"{it['자재코드']}  {it['자재명']}" for it in self.items]
                combo = ttk.Combobox(form, textvariable=sv_code, values=codes, width=28)
                combo.grid(row=0, column=1, padx=(0,20), pady=5, sticky="w")
            else:
                state = "normal" if ed else "readonly"
                ttk.Entry(form, textvariable=sv, width=30, state=state
                          ).grid(row=i, column=1, padx=(0,20), pady=5, sticky="w")

        def on_select(event=None):
            val = sv_code.get().split()[0] if sv_code.get().strip() else ""
            for it in self.items:
                if it["자재코드"] == val:
                    sv_name.set(it["자재명"])
                    sv_brand.set(it.get("브랜드",""))
                    sv_kind2.set(it.get("종류",""))
                    sv_spec.set(it.get("규격",""))
                    sv_unit.set(it.get("단위",""))
                    sv_stock.set(it.get("현재고","0"))
                    avg = it.get("평균단가","0")
                    sv_avg.set(f"{float(avg):,.1f}" if avg else "0")
                    sv_price.set(avg)  # 기본값으로 현재 평균단가
                    break

        combo.bind("<<ComboboxSelected>>", on_select)

        # 버튼
        btn_fr = tk.Frame(frame, bg=BG)
        btn_fr.pack(pady=14)

        def do_save():
            code    = sv_code.get().split()[0].strip() if sv_code.get().strip() else ""
            name    = sv_name.get().strip()
            qty_s   = sv_qty.get().strip()
            price_s = sv_price.get().strip().replace(",","")

            if not code or not name:
                messagebox.showwarning("입력 오류", "자재를 선택하세요.", parent=frame)
                return
            if not qty_s.isdigit() or int(qty_s) <= 0:
                messagebox.showwarning("입력 오류", "수량을 올바르게 입력하세요.", parent=frame)
                return
            try:
                price = float(price_s)
            except ValueError:
                messagebox.showwarning("입력 오류", "단가를 올바르게 입력하세요.", parent=frame)
                return

            qty = int(qty_s)

            for it in self.items:
                if it["자재코드"] == code:
                    cur_stock = int(it.get("현재고", 0))
                    try:
                        cur_avg = float(it.get("평균단가", 0))
                    except ValueError:
                        cur_avg = 0.0

                    if kind == "입고":
                        # 이동평균단가 재계산
                        new_avg = calc_moving_avg(cur_stock, cur_avg, qty, price)
                        it["현재고"]   = str(cur_stock + qty)
                        it["평균단가"] = str(new_avg)
                    else:
                        # 출고: 평균단가 유지, 재고만 감소
                        if cur_stock < qty:
                            messagebox.showerror("재고 부족",
                                f"현재고({cur_stock})가 출고 수량({qty})보다 적습니다.",
                                parent=frame)
                            return
                        it["현재고"] = str(cur_stock - qty)
                        # 출고단가는 현재 평균단가 사용
                        price = cur_avg
                    break

            rec = {
                "일시":     datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "종류":     kind,
                "자재코드": code,
                "자재명":   name,
                "수량":     str(qty),
                "단가":     str(round(price, 2)),
                "합계금액": str(round(qty * price, 2)),
                "담당자":   sv_who.get().strip(),
                "비고":     sv_note.get().strip(),
            }
            self.history.append(rec)
            save_csv(ITEMS_FILE,   ITEMS_HEADER,   self.items)
            save_csv(HISTORY_FILE, HISTORY_HEADER, self.history)

            self._refresh_inventory()
            self._refresh_history()

            # 폼 초기화
            for sv in (sv_code, sv_name, sv_brand, sv_kind2, sv_spec,
                       sv_unit, sv_stock, sv_avg, sv_price, sv_qty, sv_who, sv_note):
                sv.set("")
            combo["values"] = [f"{it['자재코드']}  {it['자재명']}" for it in self.items]

            messagebox.showinfo("완료", f"{kind} 등록 완료\n{name}  {qty}개", parent=frame)

        def do_clear():
            for sv in (sv_code, sv_name, sv_brand, sv_kind2, sv_spec,
                       sv_unit, sv_stock, sv_avg, sv_price, sv_qty, sv_who, sv_note):
                sv.set("")

        self._btn(btn_fr, f"{icon} {kind} 등록", do_save, bg=color, fg=BG, w=16).pack(side="left", padx=8)
        self._btn(btn_fr, "🗑️ 초기화", do_clear, bg=BTN_BG, w=10).pack(side="left", padx=8)

    # ══════════════════════════════════════════════════════════
    # 탭 4 – 입출고 기록
    # ══════════════════════════════════════════════════════════
    def _build_tab_hist(self):
        top = tk.Frame(self.f_hist, bg=BG)
        top.pack(fill="x", padx=12, pady=8)

        self._label(top, "검색:").pack(side="left")
        self._sv_hist_search = tk.StringVar()
        self._sv_hist_search.trace_add("write", lambda *_: self._refresh_history())
        self._entry(top, self._sv_hist_search, 20).pack(side="left", padx=6)

        self._sv_hist_kind = tk.StringVar(value="전체")
        for v in ("전체","입고","출고"):
            tk.Radiobutton(top, text=v, variable=self._sv_hist_kind, value=v,
                           bg=BG, fg=FG, selectcolor=BTN_BG, activebackground=BG,
                           font=("맑은 고딕",9),
                           command=self._refresh_history).pack(side="left", padx=4)

        self._btn(top, "🔄 새로고침", self._refresh_history, w=12).pack(side="left", padx=8)

        cols = ["일시","종류","자재코드","자재명","수량","단가","합계금액","담당자","비고"]
        self.tree_hist = ttk.Treeview(self.f_hist, columns=cols, show="headings")
        widths = [145, 60, 90, 150, 60, 90, 110, 80, 130]
        for c, w in zip(cols, widths):
            self.tree_hist.heading(c, text=c)
            self.tree_hist.column(c, width=w, anchor="center")

        sb = ttk.Scrollbar(self.f_hist, orient="vertical", command=self.tree_hist.yview)
        self.tree_hist.configure(yscrollcommand=sb.set)
        self.tree_hist.pack(fill="both", expand=True, padx=(12,0), pady=(0,4), side="left")
        sb.pack(side="right", fill="y", pady=(0,4), padx=(0,4))

        self.tree_hist.tag_configure("in",  foreground=GREEN)
        self.tree_hist.tag_configure("out", foreground=RED)
        self._refresh_history()

    def _refresh_history(self):
        kw   = self._sv_hist_search.get().lower()
        kind = self._sv_hist_kind.get()
        for r in self.tree_hist.get_children():
            self.tree_hist.delete(r)
        for h in reversed(self.history):
            if kind != "전체" and h.get("종류","") != kind:
                continue
            if kw and kw not in h.get("자재코드","").lower() and kw not in h.get("자재명","").lower():
                continue
            tag = "in" if h.get("종류") == "입고" else "out"
            try:
                amt   = f"{float(h.get('합계금액',0)):,.0f} 원"
                price = f"{float(h.get('단가',0)):,.1f} 원"
            except ValueError:
                amt   = h.get("합계금액","")
                price = h.get("단가","")
            self.tree_hist.insert("", "end",
                values=(h["일시"], h["종류"], h["자재코드"], h["자재명"],
                        h["수량"], price, amt, h.get("담당자",""), h.get("비고","")),
                tags=(tag,))

    # ══════════════════════════════════════════════════════════
    # 탭 5 – 자재 관리
    # ══════════════════════════════════════════════════════════
    def _build_tab_item(self):
        pane = tk.PanedWindow(self.f_item, orient="horizontal", bg=BG, sashwidth=6)
        pane.pack(fill="both", expand=True)

        # 왼쪽: 목록
        left = tk.Frame(pane, bg=BG)
        pane.add(left, minsize=520)

        cols = ["자재코드","자재명","브랜드","종류","규격","단위","현재고","평균단가","비고"]
        self.tree_item = ttk.Treeview(left, columns=cols, show="headings", selectmode="browse")
        widths2 = [90, 130, 100, 100, 90, 55, 65, 85, 110]
        for c, w in zip(cols, widths2):
            self.tree_item.heading(c, text=c)
            self.tree_item.column(c, width=w, anchor="center")
        sb2 = ttk.Scrollbar(left, orient="vertical", command=self.tree_item.yview)
        self.tree_item.configure(yscrollcommand=sb2.set)
        self.tree_item.pack(fill="both", expand=True, side="left")
        sb2.pack(side="right", fill="y")
        self.tree_item.bind("<<TreeviewSelect>>", self._on_item_select)
        self._refresh_item_list()

        # 오른쪽: 입력 폼
        right = tk.Frame(pane, bg=BG, padx=20)
        pane.add(right, minsize=300)

        tk.Label(right, text="자재 등록 / 수정",
                 font=("맑은 고딕",12,"bold"), bg=BG, fg=ACCENT).pack(pady=(16,10))

        self._item_vars = {}
        fields = [
            ("자재코드",   "code"),
            ("자재명",     "name"),
            ("브랜드",     "brand"),
            ("종류",       "kind"),
            ("규격",       "spec"),
            ("단위",       "unit"),
            ("현재고",     "stock"),
            ("안전재고",   "safe"),
            ("평균단가",   "price"),
            ("비고",       "note"),
        ]
        for label, key in fields:
            fr = tk.Frame(right, bg=BG)
            fr.pack(fill="x", pady=4)
            tk.Label(fr, text=label, bg=BG, fg=MUTED,
                     font=("맑은 고딕",10), width=9, anchor="e").pack(side="left")
            sv = tk.StringVar()
            self._item_vars[key] = sv
            ttk.Entry(fr, textvariable=sv, width=22).pack(side="left", padx=6)

        # 사진 선택
        fr_photo = tk.Frame(right, bg=BG)
        fr_photo.pack(fill="x", pady=4)
        tk.Label(fr_photo, text="사진", bg=BG, fg=MUTED,
                 font=("맑은 고딕",10), width=9, anchor="e").pack(side="left")
        self._item_vars["photo"] = tk.StringVar()
        ttk.Entry(fr_photo, textvariable=self._item_vars["photo"], width=14).pack(side="left", padx=6)
        self._btn(fr_photo, "📁 찾기", self._pick_photo, bg=BTN_BG, w=7).pack(side="left")

        # 미리보기
        self._preview_lbl = tk.Label(right, bg=BG, text="미리보기 없음", fg=MUTED,
                                     font=("맑은 고딕",9))
        self._preview_lbl.pack(pady=4)

        btn_fr = tk.Frame(right, bg=BG)
        btn_fr.pack(pady=12)
        self._btn(btn_fr, "➕ 등록",   self._item_add,    bg=GREEN,  fg=BG, w=10).pack(side="left", padx=3)
        self._btn(btn_fr, "✏️ 수정",   self._item_edit,   bg=ACCENT, fg=BG, w=10).pack(side="left", padx=3)
        self._btn(btn_fr, "🗑️ 삭제",  self._item_delete, bg=RED,    fg=BG, w=10).pack(side="left", padx=3)
        self._btn(btn_fr, "🆕 초기화", self._item_clear,  bg=BTN_BG, fg=FG, w=10).pack(side="left", padx=3)

    def _pick_photo(self):
        path = filedialog.askopenfilename(
            title="사진 선택",
            filetypes=[("이미지 파일","*.png *.jpg *.jpeg *.webp *.bmp *.gif"), ("전체","*.*")]
        )
        if path:
            self._item_vars["photo"].set(path)
            self._show_preview(path)

    def _show_preview(self, path):
        thumb = load_thumb(path)
        if thumb:
            self._preview_lbl.configure(image=thumb, text="")
            self._preview_lbl._img = thumb
        else:
            self._preview_lbl.configure(image="", text="미리보기 없음")

    def _refresh_item_list(self):
        for r in self.tree_item.get_children():
            self.tree_item.delete(r)
        for it in self.items:
            try:
                avg = f"{float(it.get('평균단가',0)):,.1f}"
            except ValueError:
                avg = it.get("평균단가","")
            self.tree_item.insert("", "end", iid=it["자재코드"],
                values=(it["자재코드"], it["자재명"], it.get("브랜드",""),
                        it.get("종류",""), it.get("규격",""), it.get("단위",""),
                        it.get("현재고",""), avg, it.get("비고","")))

    def _on_item_select(self, event=None):
        sel = self.tree_item.selection()
        if not sel:
            return
        code = sel[0]
        for it in self.items:
            if it["자재코드"] == code:
                self._item_vars["code"].set(it["자재코드"])
                self._item_vars["name"].set(it["자재명"])
                self._item_vars["brand"].set(it.get("브랜드",""))
                self._item_vars["kind"].set(it.get("종류",""))
                self._item_vars["spec"].set(it.get("규격",""))
                self._item_vars["unit"].set(it.get("단위",""))
                self._item_vars["stock"].set(it.get("현재고",""))
                self._item_vars["safe"].set(it.get("안전재고",""))
                self._item_vars["price"].set(it.get("평균단가",""))
                self._item_vars["note"].set(it.get("비고",""))
                photo = it.get("사진경로","")
                self._item_vars["photo"].set(photo)
                self._show_preview(photo)
                break

    def _item_add(self):
        v = {k: sv.get().strip() for k, sv in self._item_vars.items()}
        if not v["code"] or not v["name"]:
            messagebox.showwarning("오류", "자재코드와 자재명은 필수입니다.")
            return
        if any(it["자재코드"] == v["code"] for it in self.items):
            messagebox.showwarning("오류", f"자재코드 '{v['code']}'는 이미 존재합니다.")
            return
        new = {
            "자재코드": v["code"], "자재명": v["name"],
            "브랜드":   v["brand"], "종류":   v["kind"], "규격": v["spec"],
            "단위":     v["unit"], "현재고": v["stock"] or "0",
            "안전재고": v["safe"] or "0", "평균단가": v["price"] or "0",
            "사진경로": v["photo"], "비고": v["note"]
        }
        self.items.append(new)
        save_csv(ITEMS_FILE, ITEMS_HEADER, self.items)
        self._refresh_item_list()
        self._refresh_inventory()
        messagebox.showinfo("완료", f"자재 '{v['name']}'이(가) 등록되었습니다.")
        self._item_clear()

    def _item_edit(self):
        v = {k: sv.get().strip() for k, sv in self._item_vars.items()}
        if not v["code"]:
            messagebox.showwarning("오류", "수정할 자재를 선택하세요.")
            return
        for it in self.items:
            if it["자재코드"] == v["code"]:
                it["자재명"]   = v["name"]
                it["브랜드"]   = v["brand"]
                it["종류"]     = v["kind"]
                it["규격"]     = v["spec"]
                it["단위"]     = v["unit"]
                it["현재고"]   = v["stock"]
                it["안전재고"] = v["safe"]
                it["평균단가"] = v["price"]
                it["사진경로"] = v["photo"]
                it["비고"]     = v["note"]
                break
        save_csv(ITEMS_FILE, ITEMS_HEADER, self.items)
        self._refresh_item_list()
        self._refresh_inventory()
        messagebox.showinfo("완료", "수정되었습니다.")

    def _item_delete(self):
        v = self._item_vars["code"].get().strip()
        if not v:
            messagebox.showwarning("오류", "삭제할 자재를 선택하세요.")
            return
        name = next((it["자재명"] for it in self.items if it["자재코드"] == v), v)
        if not messagebox.askyesno("삭제 확인", f"'{name}'을(를) 삭제하시겠습니까?"):
            return
        self.items = [it for it in self.items if it["자재코드"] != v]
        save_csv(ITEMS_FILE, ITEMS_HEADER, self.items)
        self._refresh_item_list()
        self._refresh_inventory()
        self._item_clear()

    def _item_clear(self):
        for sv in self._item_vars.values():
            sv.set("")
        self._preview_lbl.configure(image="", text="미리보기 없음")

# ── 진입점 ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # Pillow 없어도 실행되도록 처리
    try:
        from PIL import Image, ImageTk
    except ImportError:
        Image = None
        ImageTk = None
        def load_thumb(path):
            return None

    app = App()
    app.mainloop()
