import os
import importlib.util
import unittest

MODULE_PATH = "/Users/mini/공구상가_재고관리/재고관리_pyside6.py"
spec = importlib.util.spec_from_file_location("inventory_app", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class InventoryLogicTests(unittest.TestCase):
    def test_stock_logic_uses_재고_field_name_instead_of_현재고(self):
        self.assertIn("재고", module.STOCK_FIELDS)
        self.assertNotIn("현재고", module.STOCK_FIELDS)

        stock_rows = [{
            "자재명": "테스트날",
            "브랜드": "브랜드D",
            "종류": "칼날",
            "규격": "18mm",
            "단위": "개",
            "재고": "10",
            "평균단가": "1000",
            "사진경로": "",
            "비고": "",
            "위치": "D-01",
        }]
        history_rows = []
        outbound_data = {"수량": 2, "단가": 1400, "담당자": "judy", "비고": "현시세 반영"}

        module.apply_outbound_to_stock(stock_rows, history_rows, 0, outbound_data, now_str="2026-04-29 02:00:00")

        self.assertEqual(stock_rows[0]["재고"], "8")
        self.assertNotIn("현재고", stock_rows[0])
        self.assertEqual(history_rows[0]["단가"], "1400")
        self.assertEqual(history_rows[0]["금액"], str(2 * 1400))

    def test_natural_history_link_validation_accepts_inbound_then_outbound_matching_stock(self):
        stock_rows = [{
            "자재명": "테스트볼트",
            "브랜드": "브랜드A",
            "종류": "볼트",
            "규격": "M8x20",
            "단위": "개",
            "재고": "7",
            "평균단가": "100",
            "사진경로": "",
            "비고": "",
            "위치": "A-01",
        }]
        history_rows = [
            {"일시": "2026-04-01 09:00:00", "구분": "입고", "자재명": "테스트볼트", "브랜드": "브랜드A", "종류": "볼트", "규격": "M8x20", "수량": "10", "단가": "100", "금액": "1000", "담당자": "judy", "비고": "초도입고"},
            {"일시": "2026-04-03 11:00:00", "구분": "출고", "자재명": "테스트볼트", "브랜드": "브랜드A", "종류": "볼트", "규격": "M8x20", "수량": "3", "단가": "120", "금액": "360", "담당자": "judy", "비고": "판매"},
        ]

        self.assertTrue(module.is_naturally_linked_inventory(stock_rows, history_rows))

    def test_natural_history_link_validation_rejects_outbound_before_any_inbound(self):
        stock_rows = [{
            "자재명": "테스트너트",
            "브랜드": "브랜드B",
            "종류": "너트",
            "규격": "M10",
            "단위": "개",
            "재고": "1",
            "평균단가": "80",
            "사진경로": "",
            "비고": "",
            "위치": "B-01",
        }]
        history_rows = [
            {"일시": "2026-04-01 09:00:00", "구분": "출고", "자재명": "테스트너트", "브랜드": "브랜드B", "종류": "너트", "규격": "M10", "수량": "1", "단가": "100", "금액": "100", "담당자": "judy", "비고": "오류샘플"},
            {"일시": "2026-04-02 09:00:00", "구분": "입고", "자재명": "테스트너트", "브랜드": "브랜드B", "종류": "너트", "규격": "M10", "수량": "2", "단가": "80", "금액": "160", "담당자": "judy", "비고": "늦은입고"},
        ]

        self.assertFalse(module.is_naturally_linked_inventory(stock_rows, history_rows))

    def test_outbound_uses_input_price_for_history(self):
        stock_rows = [{
            "자재명": "테스트날",
            "브랜드": "브랜드D",
            "종류": "칼날",
            "규격": "18mm",
            "단위": "개",
            "재고": "10",
            "평균단가": "1000",
            "사진경로": "",
            "비고": "",
            "위치": "D-01",
        }]
        history_rows = []
        outbound_data = {"수량": 2, "단가": 1400, "담당자": "judy", "비고": "현시세 반영"}

        module.apply_outbound_to_stock(stock_rows, history_rows, 0, outbound_data, now_str="2026-04-29 02:00:00")

        self.assertEqual(stock_rows[0]["재고"], "8")
        self.assertEqual(history_rows[0]["단가"], "1400")
        self.assertEqual(history_rows[0]["금액"], str(2 * 1400))

    def test_stock_filter_layout_config_is_content_sized_row(self):
        config = module.stock_filter_layout_config()
        self.assertEqual(config["layout_mode"], "row")
        self.assertTrue(config["add_trailing_stretch"])
        self.assertEqual(config["item_spacing"], 88)
        self.assertEqual(config["row_spacing"], 16)
        self.assertEqual(config["button_min_width"], 93)
        self.assertEqual(config["clear_width"], 20)
        self.assertEqual(config["field_right_margin"], 0)

    def test_filter_option_values_support_search(self):
        values = ["전체", "보쉬", "밀워키", "마끼다"]
        self.assertEqual(module.filter_option_values(values, "보"), ["보쉬"])
        self.assertEqual(module.filter_option_values(values, ""), values)

    def test_clear_stock_filter_resets_single_field_only(self):
        filters = {"브랜드": "보쉬", "종류": "절삭공구", "자재명": "전체", "규격": "", "위치": "B-02"}
        result = module.clear_stock_filter(filters, "종류")
        self.assertEqual(result["종류"], "전체")
        self.assertEqual(result["브랜드"], "보쉬")
        self.assertEqual(result["위치"], "B-02")

    def test_active_filter_summary_shows_only_selected_filters(self):
        filters = {"브랜드": "보쉬", "종류": "전체", "자재명": "드릴비트", "규격": "", "위치": "B-02"}
        text = module.active_filter_summary(filters)
        self.assertIn("브랜드: 보쉬", text)
        self.assertIn("품명: 드릴비트", text)
        self.assertIn("위치: B-02", text)
        self.assertNotIn("종류", text)

    def test_active_filter_summary_returns_default_when_empty(self):
        filters = {"브랜드": "전체", "종류": "", "자재명": "전체", "규격": "", "위치": "전체"}
        self.assertEqual(module.active_filter_summary(filters), "적용 필터 없음")

    def test_distinct_values_returns_sorted_unique_non_empty_values(self):
        rows = [
            {"브랜드": "보쉬"},
            {"브랜드": ""},
            {"브랜드": "밀워키"},
            {"브랜드": "보쉬"},
        ]
        self.assertEqual(module.distinct_values(rows, "브랜드"), ["밀워키", "보쉬"])

    def test_stock_filter_combines_search_and_dropdown_filters(self):
        rows = [
            {"자재명": "볼트", "브랜드": "브랜드A", "종류": "볼트", "규격": "M8", "단위": "개", "재고": "1", "평균단가": "100", "사진경로": "", "비고": "", "위치": "A-01"},
            {"자재명": "너트", "브랜드": "브랜드A", "종류": "너트", "규격": "M10", "단위": "개", "재고": "1", "평균단가": "100", "사진경로": "", "비고": "", "위치": "B-01"},
            {"자재명": "볼트", "브랜드": "브랜드B", "종류": "볼트", "규격": "M10", "단위": "개", "재고": "1", "평균단가": "100", "사진경로": "", "비고": "", "위치": "A-01"},
        ]
        filters = {"브랜드": "브랜드A", "종류": "볼트", "자재명": "전체", "규격": "전체", "위치": "A-01"}
        result = module.filter_stock_rows(rows, "", filters)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["브랜드"], "브랜드A")
        self.assertEqual(result[0]["종류"], "볼트")

    def test_item_picker_filter_returns_original_indexes(self):
        rows = [
            {"자재명": "볼트", "브랜드": "브랜드A", "종류": "볼트", "규격": "M8", "단위": "개", "재고": "1", "평균단가": "100", "사진경로": "", "비고": "일반", "위치": "A-01"},
            {"자재명": "너트", "브랜드": "브랜드A", "종류": "너트", "규격": "M10", "단위": "개", "재고": "1", "평균단가": "100", "사진경로": "", "비고": "스텐", "위치": "B-01"},
            {"자재명": "볼트", "브랜드": "브랜드B", "종류": "볼트", "규격": "M10", "단위": "개", "재고": "1", "평균단가": "100", "사진경로": "", "비고": "특가", "위치": "A-01"},
        ]
        filters = {"브랜드": "브랜드B", "종류": "볼트", "자재명": "전체", "규격": "M10", "위치": "A-01"}

        result = module.filter_stock_indexed_rows(rows, "특가", filters)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 2)
        self.assertEqual(result[0][1]["브랜드"], "브랜드B")
        self.assertEqual(result[0][1]["비고"], "특가")

    def test_item_picker_filter_summary_reuses_stock_filter_summary(self):
        filters = {"브랜드": "브랜드A", "종류": "전체", "자재명": "볼트", "규격": "M8", "위치": "A-01"}
        self.assertEqual(
            module.active_filter_summary(filters),
            "브랜드: 브랜드A / 품명: 볼트 / 규격: M8 / 위치: A-01"
        )

    def test_inout_action_labels_use_new_item_wording(self):
        self.assertEqual(module.INOUT_NEW_ITEM_BUTTON_TEXT, "신규 품목 입고 등록")
        self.assertEqual(module.NEW_ITEM_INBOUND_DIALOG_TITLE, "신규 품목 입고 등록")

    def test_app_stylesheet_contains_fixed_text_colors_for_theme_independent_ui(self):
        stylesheet = module.app_stylesheet()
        self.assertIn("QLabel { color: #111827; }", stylesheet)
        self.assertIn("QLineEdit, QComboBox, QSpinBox, QTextEdit {", stylesheet)
        self.assertIn("color: #111827;", stylesheet)
        self.assertIn("QTableWidget {", stylesheet)
        self.assertIn("QListWidget {", stylesheet)
        self.assertIn("QMenuBar {", stylesheet)
        self.assertIn("QMenu {", stylesheet)

    def test_app_stylesheet_keeps_fixed_colors_for_table_and_menu_selection(self):
        stylesheet = module.app_stylesheet()
        self.assertIn("QMenu::item:selected {", stylesheet)
        self.assertIn("QTableWidget {", stylesheet)
        self.assertIn("QListWidget {", stylesheet)
        self.assertIn("selection-color: #0f172a;", stylesheet)
        self.assertIn("color: #111827;", stylesheet)

    def test_app_stylesheet_uses_fixed_white_theme_backgrounds(self):
        stylesheet = module.app_stylesheet()
        self.assertIn("QMainWindow { background: #f3f6fa; color: #111827; }", stylesheet)
        self.assertIn("QDialog { background: #f3f6fa; color: #111827; }", stylesheet)
        self.assertIn("QMenuBar {", stylesheet)
        self.assertIn("background: #f3f6fa;", stylesheet)

    def test_app_stylesheet_makes_table_row_selection_visible_even_without_focus(self):
        stylesheet = module.app_stylesheet()
        self.assertIn("QTableWidget::item:selected {", stylesheet)
        self.assertIn("QTableWidget::item:selected:active {", stylesheet)
        self.assertIn("QTableWidget::item:selected:!active {", stylesheet)
        self.assertIn("background: #93c5fd;", stylesheet)
        self.assertIn("border: 1px solid #2563eb;", stylesheet)
        self.assertIn("color: #0f172a;", stylesheet)

    def test_app_stylesheet_uses_softer_header_card_border_and_button_tones(self):
        stylesheet = module.app_stylesheet()
        self.assertIn("QHeaderView::section {", stylesheet)
        self.assertIn("background: #dce6f2;", stylesheet)
        self.assertIn("QFrame#Card {", stylesheet)
        self.assertIn("border: 1px solid #d9e2ec;", stylesheet)
        self.assertIn("QPushButton {", stylesheet)
        self.assertIn("background: #3b82c4;", stylesheet)
        self.assertIn("QPushButton:hover { background: #2f6fa8; }", stylesheet)
        self.assertIn("QPushButton:pressed { background: #285f90; }", stylesheet)

    def test_fixed_palette_uses_white_window_and_stronger_highlight(self):
        palette = module.build_fixed_palette()
        self.assertEqual(palette.color(module.QPalette.Window).name(), "#f3f6fa")
        self.assertEqual(palette.color(module.QPalette.Base).name(), "#ffffff")
        self.assertEqual(palette.color(module.QPalette.Highlight).name(), "#93c5fd")
        self.assertEqual(palette.color(module.QPalette.HighlightedText).name(), "#0f172a")

    def test_stock_search_matches_brand_kind_name_spec_and_note_location(self):
        rows = [{
            "자재명": "테스트볼트",
            "브랜드": "브랜드A",
            "종류": "볼트",
            "규격": "M8x20",
            "단위": "개",
            "재고": "10",
            "평균단가": "100",
            "사진경로": "",
            "비고": "특가",
            "위치": "A-01",
        }]

        self.assertEqual(len(module.filter_stock_rows(rows, "브랜드A")), 1)
        self.assertEqual(len(module.filter_stock_rows(rows, "볼트")), 1)
        self.assertEqual(len(module.filter_stock_rows(rows, "테스트")), 1)
        self.assertEqual(len(module.filter_stock_rows(rows, "M8x20")), 1)
        self.assertEqual(len(module.filter_stock_rows(rows, "특가")), 1)
        self.assertEqual(len(module.filter_stock_rows(rows, "A-01")), 1)
        self.assertEqual(len(module.filter_stock_rows(rows, "없는값")), 0)

    def test_history_search_matches_note_and_filters_kind(self):
        rows = [
            {"일시": "2026-04-29 01:00:00", "구분": "입고", "자재명": "볼트", "브랜드": "A", "종류": "볼트", "규격": "M8", "수량": "10", "단가": "100", "금액": "1000", "담당자": "", "비고": "첫입고"},
            {"일시": "2026-04-29 01:10:00", "구분": "출고", "자재명": "너트", "브랜드": "B", "종류": "너트", "규격": "M10", "수량": "2", "단가": "50", "금액": "100", "담당자": "", "비고": "급출고"},
        ]

        self.assertEqual(len(module.filter_history_rows(rows, "", "전체")), 2)
        self.assertEqual(len(module.filter_history_rows(rows, "첫입고", "전체")), 1)
        self.assertEqual(len(module.filter_history_rows(rows, "급출고", "출고")), 1)
        self.assertEqual(len(module.filter_history_rows(rows, "급출고", "입고")), 0)

    def test_page_jump_target_clamps_within_total_page_range(self):
        self.assertEqual(module.clamp_page_number(0, 67), 1)
        self.assertEqual(module.clamp_page_number(1, 67), 1)
        self.assertEqual(module.clamp_page_number(15, 67), 15)
        self.assertEqual(module.clamp_page_number(999, 67), 67)
        self.assertEqual(module.clamp_page_number(5, 0), 1)

    def test_pagination_summary_includes_direct_page_jump_hint(self):
        text = module.stock_pagination_summary(1, 67)
        self.assertEqual(text, "1 / 67 페이지")

    def test_history_kind_colors_use_light_backgrounds_with_black_text(self):
        inbound_style = module.history_kind_colors("입고")
        outbound_style = module.history_kind_colors("출고")
        other_style = module.history_kind_colors("기타")

        self.assertEqual(inbound_style, ("#dcfce7", "#111827"))
        self.assertEqual(outbound_style, ("#fee2e2", "#111827"))
        self.assertIsNone(other_style)

    def test_history_kind_badge_stylesheet_uses_visible_colored_background(self):
        inbound_style = module.history_kind_badge_stylesheet("입고")
        outbound_style = module.history_kind_badge_stylesheet("출고")
        fallback_style = module.history_kind_badge_stylesheet("기타")

        self.assertIn("background: #dcfce7;", inbound_style)
        self.assertIn("color: #111827;", inbound_style)
        self.assertIn("background: #fee2e2;", outbound_style)
        self.assertIn("color: #111827;", outbound_style)
        self.assertIn("background: transparent;", fallback_style)

    def test_refresh_history_table_renders_kind_column_as_colored_badge_widget(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        win.history_rows = [
            {"일시": "2026-04-29 01:00:00", "구분": "입고", "자재명": "볼트", "브랜드": "A", "종류": "볼트", "규격": "M8", "수량": "10", "단가": "100", "금액": "1000", "담당자": "", "비고": "첫입고"},
            {"일시": "2026-04-29 01:10:00", "구분": "출고", "자재명": "너트", "브랜드": "B", "종류": "너트", "규격": "M10", "수량": "2", "단가": "50", "금액": "100", "담당자": "", "비고": "급출고"},
        ]
        win.refresh_history_table()

        inbound_widget = win.history_table.cellWidget(1, 1)
        outbound_widget = win.history_table.cellWidget(0, 1)

        self.assertIsNotNone(inbound_widget)
        self.assertIsNotNone(outbound_widget)
        self.assertIn("background: #dcfce7;", inbound_widget.styleSheet())
        self.assertIn("background: #fee2e2;", outbound_widget.styleSheet())

        win.close()
        app.quit()

    def test_stock_page_size_stays_15_without_forcing_15_row_table_height(self):
        self.assertEqual(module.STOCK_PAGE_SIZE, 15)

    def test_stock_tab_does_not_force_table_minimum_height_to_15_rows(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertLess(win.stock_table.minimumHeight(), module.stock_table_visible_height(win.stock_table.verticalHeader().defaultSectionSize()))

        win.close()
        app.quit()

    def test_stock_tab_removes_main_grid_description_sentence(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        stock_tab = win.tabs.widget(0)
        label_texts = [label.text() for label in stock_tab.findChildren(module.QLabel)]

        self.assertNotIn(
            "브랜드, 종류, 품명, 규격, 재고, 평균단가, 위치, 비고 정보를 검색하고 관리하는 메인 그리드입니다.",
            label_texts,
        )

        win.close()
        app.quit()

    def test_stock_tab_search_card_uses_tighter_vertical_margins(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        stock_tab = win.tabs.widget(0)
        toolbar_card = next(
            frame for frame in stock_tab.findChildren(module.QFrame)
            if frame.objectName() == "Card" and frame.layout() is not None
        )
        margins = toolbar_card.layout().contentsMargins()

        self.assertEqual((margins.left(), margins.top(), margins.right(), margins.bottom()), (16, 12, 16, 12))

        win.close()
        app.quit()

    def test_stock_tab_uses_scrollable_table_again_instead_of_fixed_15_row_height(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertEqual(win.stock_table.verticalScrollBarPolicy(), module.Qt.ScrollBarAsNeeded)
        self.assertGreater(win.stock_table.maximumHeight(), module.stock_table_visible_height(win.stock_table.verticalHeader().defaultSectionSize()))

        win.close()
        app.quit()

    def test_history_table_selects_full_row_like_stock_table(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertEqual(win.history_table.selectionBehavior(), module.QAbstractItemView.SelectRows)

        win.close()
        app.quit()

    def test_history_tab_paginates_15_rows_per_page_like_stock_tab(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        win.history_rows = [
            {
                "일시": f"2026-05-01 09:{i:02d}:00",
                "구분": "입고" if i % 2 == 0 else "출고",
                "자재명": f"테스트품목{i}",
                "브랜드": "브랜드A",
                "종류": "공구",
                "규격": "M8",
                "수량": str(i + 1),
                "단가": "1000",
                "금액": str((i + 1) * 1000),
                "담당자": "judy",
                "비고": "테스트",
                "위치": f"A-{i:02d}",
            }
            for i in range(40)
        ]
        win.current_history_page = 1
        win.refresh_history_table()

        self.assertEqual(win.history_table.rowCount(), 15)
        self.assertEqual(win.history_page_label.text(), "1 / 3 페이지")
        self.assertEqual(win.history_page_jump_input.text(), "1")

        win.go_to_history_page(3)

        self.assertEqual(win.history_table.rowCount(), 10)
        self.assertEqual(win.history_page_label.text(), "3 / 3 페이지")
        self.assertEqual(win.history_page_jump_input.text(), "3")

        win.close()
        app.quit()

    def test_history_tab_uses_stock_like_filter_buttons_and_summary(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertEqual(list(win.history_filter_buttons.keys()), ["브랜드", "종류", "자재명", "규격", "위치"])
        self.assertEqual(win.history_filter_summary_label.text(), "적용 필터 없음")
        self.assertEqual(win.history_page_jump_input.width(), win.page_jump_input.width())

        win.close()
        app.quit()

    def test_filter_history_rows_supports_stock_like_field_filters(self):
        rows = [
            {"일시": "2026-05-01 09:00:00", "구분": "입고", "자재명": "드릴", "브랜드": "보쉬", "종류": "전동공구", "규격": "10mm", "수량": "1", "단가": "1000", "금액": "1000", "담당자": "judy", "비고": "신규", "위치": "A-01"},
            {"일시": "2026-05-01 10:00:00", "구분": "입고", "자재명": "드릴", "브랜드": "마끼다", "종류": "전동공구", "규격": "10mm", "수량": "1", "단가": "1000", "금액": "1000", "담당자": "judy", "비고": "신규", "위치": "B-01"},
            {"일시": "2026-05-01 11:00:00", "구분": "출고", "자재명": "비트", "브랜드": "보쉬", "종류": "절삭공구", "규격": "6mm", "수량": "1", "단가": "1000", "금액": "1000", "담당자": "judy", "비고": "출고", "위치": "A-01"},
        ]

        filtered = module.filter_history_rows(rows, "", "전체", {"브랜드": "보쉬", "위치": "A-01"})

        self.assertEqual(len(filtered), 2)
        self.assertTrue(all(row["브랜드"] == "보쉬" for row in filtered))
        self.assertTrue(all(row["위치"] == "A-01" for row in filtered))

    def test_history_kind_combo_reserves_enough_width_for_korean_text(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertEqual(win.history_kind.sizeAdjustPolicy(), module.QComboBox.AdjustToContents)
        self.assertGreaterEqual(win.history_kind.minimumContentsLength(), 4)

        win.close()
        app.quit()

    def test_stock_tab_search_row_keeps_only_search_and_reset_controls(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        stock_tab = win.tabs.widget(0)
        row_buttons = [button.text() for button in stock_tab.findChildren(module.QPushButton)]

        self.assertNotIn("Search", row_buttons)
        self.assertIn("초기화", row_buttons)

        win.close()
        app.quit()

    def test_history_tab_search_row_keeps_only_filter_and_reset_controls(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        history_tab = win.tabs.widget(2)
        row_buttons = [button.text() for button in history_tab.findChildren(module.QPushButton)]

        self.assertNotIn("조회", row_buttons)
        self.assertIn("초기화", row_buttons)

        win.close()
        app.quit()

    def test_search_rows_use_natural_compact_spacing_after_button_removal(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        stock_tab = win.tabs.widget(0)
        history_tab = win.tabs.widget(2)
        stock_line = win.stock_search.parentWidget()
        history_line = win.history_search.parentWidget()

        self.assertIsNotNone(stock_line)
        self.assertIsNotNone(history_line)
        self.assertEqual(stock_line.layout().spacing(), 8)
        self.assertEqual(history_line.layout().spacing(), 8)

        win.close()
        app.quit()

    def test_main_window_keeps_vertical_resize_enabled(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertGreater(win.maximumHeight(), win.minimumHeight())
        self.assertGreater(win.maximumHeight(), win.height())

        win.close()
        app.quit()

    def test_new_item_dialog_offers_saved_value_picker_buttons_for_main_fields(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        dialog = module.ItemDialog(win)

        for field_name in ["브랜드", "종류", "자재명", "규격", "단위", "위치"]:
            self.assertIn(field_name, dialog.select_buttons)
            self.assertEqual(dialog.select_buttons[field_name].text(), "선택")

        dialog.close()
        win.close()
        app.quit()

    def test_stock_tab_bottom_row_places_page_group_left_and_actions_right_with_equal_widths(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertEqual(win.page_jump_input.width(), 64)
        bottom_layout = win.page_label.parentWidget().parentWidget().layout()
        self.assertEqual(bottom_layout.spacing(), 6)

        stock_buttons = {button.text(): button for button in win.tabs.widget(0).findChildren(module.QPushButton)}
        self.assertEqual(stock_buttons["변경"].property("role"), "primary-strong")
        self.assertEqual(stock_buttons["이전"].property("role"), "secondary")
        self.assertEqual(stock_buttons["다음"].property("role"), "secondary")

        page_group = win.page_label.parentWidget()
        self.assertTrue(page_group.property("bottomGroup"))
        self.assertEqual(page_group.layout().spacing(), 6)
        margins = page_group.layout().contentsMargins()
        self.assertEqual((margins.left(), margins.top(), margins.right(), margins.bottom()), (12, 3, 12, 3))
        page_group_texts = []
        for i in range(page_group.layout().count()):
            widget = page_group.layout().itemAt(i).widget()
            if isinstance(widget, module.QLabel):
                page_group_texts.append(widget.text())
            elif isinstance(widget, module.QLineEdit):
                page_group_texts.append("페이지입력")
            elif isinstance(widget, module.QPushButton):
                page_group_texts.append(widget.text())
        self.assertEqual(page_group_texts, [win.page_label.text(), "페이지입력", "이동"])

        self.assertEqual(stock_buttons["이동"].width(), stock_buttons["이전"].width())
        self.assertEqual(stock_buttons["이동"].width(), stock_buttons["다음"].width())
        self.assertEqual(stock_buttons["이동"].width(), stock_buttons["변경"].width())
        self.assertGreaterEqual(stock_buttons["이동"].width(), 150)

        ordered_texts = []
        stretch_indexes = []
        for i in range(bottom_layout.count()):
            item = bottom_layout.itemAt(i)
            widget = item.widget()
            if widget is None:
                if item.spacerItem() is not None:
                    stretch_indexes.append(i)
                continue
            if widget.property("bottomGroup"):
                ordered_texts.append("그룹")
            elif isinstance(widget, module.QPushButton):
                ordered_texts.append(widget.text())
        self.assertEqual(ordered_texts, ["그룹", "이전", "다음", "변경"])
        self.assertEqual(stretch_indexes, [1])

        win.close()
        app.quit()

    def test_history_tab_bottom_row_places_page_group_left_and_actions_right_with_equal_widths(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()

        self.assertEqual(win.history_page_jump_input.width(), 64)
        bottom_layout = win.history_page_label.parentWidget().parentWidget().layout()
        self.assertEqual(bottom_layout.spacing(), 6)

        page_group = win.history_page_label.parentWidget()
        self.assertTrue(page_group.property("bottomGroup"))
        self.assertEqual(page_group.layout().spacing(), 6)
        margins = page_group.layout().contentsMargins()
        self.assertEqual((margins.left(), margins.top(), margins.right(), margins.bottom()), (12, 3, 12, 3))
        page_group_texts = []
        for i in range(page_group.layout().count()):
            widget = page_group.layout().itemAt(i).widget()
            if isinstance(widget, module.QLabel):
                page_group_texts.append(widget.text())
            elif isinstance(widget, module.QLineEdit):
                page_group_texts.append("페이지입력")
            elif isinstance(widget, module.QPushButton):
                page_group_texts.append(widget.text())
        self.assertEqual(page_group_texts, [win.history_page_label.text(), "페이지입력", "이동"])

        history_buttons = {button.text(): button for button in win.tabs.widget(2).findChildren(module.QPushButton)}
        self.assertEqual(history_buttons["이동"].width(), history_buttons["이전"].width())
        self.assertEqual(history_buttons["이동"].width(), history_buttons["다음"].width())
        self.assertGreaterEqual(history_buttons["이동"].width(), 150)

        ordered_texts = []
        stretch_indexes = []
        for i in range(bottom_layout.count()):
            item = bottom_layout.itemAt(i)
            widget = item.widget()
            if widget is None:
                if item.spacerItem() is not None:
                    stretch_indexes.append(i)
                continue
            if widget.property("bottomGroup"):
                ordered_texts.append("그룹")
            elif isinstance(widget, module.QPushButton):
                ordered_texts.append(widget.text())
        self.assertEqual(ordered_texts, ["그룹", "이전", "다음"])
        self.assertEqual(stretch_indexes, [1])

        win.close()
        app.quit()

    def test_stock_and_history_tables_use_rebalanced_column_widths(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        win.refresh_stock_table()
        win.refresh_history_table()

        self.assertLessEqual(win.stock_table.columnWidth(0), 44)
        self.assertGreaterEqual(win.stock_table.columnWidth(3), 170)
        self.assertLessEqual(win.stock_table.columnWidth(6), 58)
        self.assertLessEqual(win.stock_table.columnWidth(9), 170)

        self.assertGreaterEqual(win.history_table.columnWidth(0), 170)
        self.assertLessEqual(win.history_table.columnWidth(1), 70)
        self.assertLessEqual(win.history_table.columnWidth(10), 170)

        win.close()
        app.quit()

    def test_inout_tab_uses_compact_cards_and_primary_secondary_button_hierarchy(self):
        app = module.QApplication.instance() or module.QApplication([])
        win = module.IMSInventoryApp()
        inout_tab = win.tabs.widget(1)
        labels = [label.text() for label in inout_tab.findChildren(module.QLabel)]
        buttons = {button.text(): button for button in inout_tab.findChildren(module.QPushButton)}

        self.assertNotIn("신규 자재 입고, 기존 품목 입고, 출고 처리를 한 화면에서 관리합니다.", labels)
        self.assertNotIn("신규 자재 입고 또는 등록된 품목 입고를 선택해서 처리합니다.", labels)
        self.assertNotIn("등록된 품목을 선택해서 출고 처리합니다. 필요하면 출고 시 단가를 직접 입력할 수 있습니다.", labels)
        self.assertEqual(buttons[module.INOUT_NEW_ITEM_BUTTON_TEXT].property("role"), "secondary")
        self.assertEqual(buttons["등록된 품목 선택 후 입고 등록"].property("role"), "primary-strong")
        self.assertEqual(buttons["등록된 품목 선택 후 출고 등록"].property("role"), "primary-strong")

        card_frames = [frame for frame in inout_tab.findChildren(module.QFrame) if frame.objectName() == "Card"]
        inner_cards = [frame for frame in card_frames if frame.layout() and frame.layout().spacing() == 8]
        self.assertGreaterEqual(len(inner_cards), 2)

        win.close()
        app.quit()

    def test_outbound_error_message_is_human_friendly(self):
        message = module.outbound_shortage_message("테스트볼트", 5, 8, "개")
        self.assertIn("재고가 부족합니다", message)
        self.assertIn("테스트볼트", message)
        self.assertIn("재고: 5개", message)
        self.assertIn("출고요청: 8개", message)

    def test_new_item_inbound_creates_stock_and_history(self):
        stock_rows = []
        history_rows = []
        item_data = {
            "자재명": "테스트볼트",
            "브랜드": "브랜드A",
            "종류": "볼트",
            "규격": "M8x20",
            "단위": "개",
            "재고": "0",
            "평균단가": "0",
            "사진경로": "",
            "비고": "신규",
            "위치": "A-01",
        }
        inbound_data = {"수량": 15, "단가": 120, "담당자": "judy", "비고": "첫입고"}

        module.create_new_item_inbound(stock_rows, history_rows, item_data, inbound_data, now_str="2026-04-29 01:00:00")

        self.assertEqual(len(stock_rows), 1)
        self.assertEqual(stock_rows[0]["재고"], "15")
        self.assertEqual(stock_rows[0]["평균단가"], "120")
        self.assertEqual(len(history_rows), 1)
        self.assertEqual(history_rows[0]["구분"], "입고")
        self.assertEqual(history_rows[0]["수량"], "15")
        self.assertEqual(history_rows[0]["단가"], "120")
        self.assertEqual(history_rows[0]["금액"], "1800")
        self.assertEqual(history_rows[0]["비고"], "첫입고")

    def test_existing_outbound_updates_stock_and_history_with_input_price(self):
        stock_rows = [{
            "자재명": "테스트드릴",
            "브랜드": "브랜드B",
            "종류": "공구",
            "규격": "8mm",
            "단위": "개",
            "재고": "20",
            "평균단가": "3500",
            "사진경로": "",
            "비고": "",
            "위치": "B-02",
        }]
        history_rows = []
        outbound_data = {"수량": 3, "단가": 9999, "담당자": "judy", "비고": "판매"}

        module.apply_outbound_to_stock(stock_rows, history_rows, 0, outbound_data, now_str="2026-04-29 01:10:00")

        self.assertEqual(stock_rows[0]["재고"], "17")
        self.assertEqual(len(history_rows), 1)
        self.assertEqual(history_rows[0]["구분"], "출고")
        self.assertEqual(history_rows[0]["단가"], "9999")
        self.assertEqual(history_rows[0]["금액"], str(3 * 9999))

    def test_existing_inbound_updates_stock_and_history(self):
        stock_rows = [{
            "자재명": "와셔",
            "브랜드": "브랜드C",
            "종류": "부속",
            "규격": "M10",
            "단위": "개",
            "재고": "10",
            "평균단가": "100",
            "사진경로": "",
            "비고": "",
            "위치": "C-01",
        }]
        history_rows = []
        inbound_data = {"수량": 10, "단가": 200, "담당자": "judy", "비고": "추가입고"}

        module.apply_inbound_to_stock(stock_rows, history_rows, 0, inbound_data, now_str="2026-04-29 01:20:00")

        self.assertEqual(stock_rows[0]["재고"], "20")
        self.assertEqual(stock_rows[0]["평균단가"], "150")
        self.assertEqual(len(history_rows), 1)
        self.assertEqual(history_rows[0]["구분"], "입고")
        self.assertEqual(history_rows[0]["단가"], "200")


if __name__ == "__main__":
    unittest.main()
