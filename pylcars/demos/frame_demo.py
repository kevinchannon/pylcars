# -*- coding: utf-8 -*-
"""C-Style (TBL) frame demo.

Demonstrates Frame with borders={TOP, BOTTOM, LEFT} — the classic C-Style.

Run with:
    python -m pylcars.demos.c_style_frame_demo
"""
import math
import sys
from PyQt5 import QtCore, QtWidgets

import pylcars


class CStyleFrameDemo(pylcars.Lcars):

    def __init__(self, parent=None):
        pylcars.Lcars.__init__(self, parent)

        self.frame = pylcars.Frame(
            self,
            QtCore.QRect(0, 0, 800, 480),
            borders={pylcars.FrameBorder.TOP, pylcars.FrameBorder.BOTTOM, pylcars.FrameBorder.LEFT},
            left_upper_buttons=["ALPHA", "BETA", "GAMMA", "PLOT", "GAUGE"],
            left_lower_buttons=["SPLIT PILLS", "INFO", "QUIT"],
            header_text="C-STYLE",
            footer_text="DEMO",
            color=pylcars.Colors.orange,
            color_active=pylcars.Colors.leuchtblau,
        )

        dr = self.frame.display_rect()

        self._build_page("ALPHA", pylcars.Colors.orange,     "ALPHA")
        self._build_page("BETA",  pylcars.Colors.flieder,    "BETA")
        self._build_page("GAMMA", pylcars.Colors.leuchtblau, "GAMMA")
        self._build_plot_page(dr)
        self._build_gauge_page(dr)
        self._build_split_pill_page(dr)
        self._build_info_page(dr)
        self._build_quit_page(dr)

        self.frame.blend_in(self.frame.active_page)

    def _build_page(self, name: str, color: str, label_text: str) -> None:
        dr = self.frame.display_rect()
        lbl = pylcars.Textline(self, dr, color, 72)
        lbl.setText(label_text)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.hide()
        self.frame.pages[name]["label"] = lbl

    def _build_plot_page(self, dr: QtCore.QRect) -> None:
        pad = 10
        plot = pylcars.Plot(
            self,
            QtCore.QRect(dr.x() + pad, dr.y() + pad, dr.width() - 2 * pad, dr.height() - 2 * pad),
            pylcars.Colors.leuchtblau,
            grid=True,
            log_x=True,
            log_y=True,
        )
        n = 50
        xs = [0.1 * (10000 ** (i / (n - 1))) for i in range(n)]  # log-spaced 0.1 → 1000
        plot.add_series((xs, [x ** 0.5 for x in xs]))   # slope 0.5 on log-log
        plot.add_series((xs, [x ** 1.5 for x in xs]))   # slope 1.5 on log-log
        plot.hide()
        self.frame.pages["PLOT"]["plot"] = plot

    def _build_gauge_page(self, dr: QtCore.QRect) -> None:
        pad = 10
        spacing = 20
        y = dr.y() + pad
        h = dr.height() - 2 * pad

        temp_cfg = pylcars.GaugeConfig(
            range=(0, 35), interval=5,
            title="TEMP", unit="°C",
            zones=[
                pylcars.ZoneInterval(start=0,  colour=pylcars.Colors.leuchtblau, thickness=6),
                pylcars.ZoneInterval(start=20, colour=pylcars.Colors.hellorange,  thickness=6),
                pylcars.ZoneInterval(start=30, colour=pylcars.Colors.rot,         thickness=8),
            ],
        )
        rain_cfg = pylcars.GaugeConfig(
            range=(0, 100), interval=10,
            title="RAINFALL", unit="mm",
            zones=[
                pylcars.ZoneInterval(start=0,  colour=pylcars.Colors.blaugrau,  thickness=6),
                pylcars.ZoneInterval(start=60, colour=pylcars.Colors.flieder,    thickness=6),
                pylcars.ZoneInterval(start=85, colour=pylcars.Colors.rot,        thickness=8),
            ],
        )

        # Left-only gauge
        g_left = pylcars.LinearGauge(
            self, QtCore.QRect(dr.x() + pad, y, dr.width(), h),
            pylcars.Colors.orange, mode="left", title="TEMP", left=temp_cfg,
        )
        g_left.set_value("left", 25)

        # Dual gauge — positioned immediately to the right of the left gauge
        dual_x = g_left.rect.x() + g_left.rect.width() + spacing
        g_dual = pylcars.LinearGauge(
            self, QtCore.QRect(dual_x, y, dr.width(), h),
            pylcars.Colors.orange, mode="dual", title="CURRENT",
            left=temp_cfg, right=rain_cfg,
        )
        g_dual.set_value("left",  25)
        g_dual.set_value("right", 80)

        # Right-only gauge — positioned immediately to the right of the dual gauge
        right_x = g_dual.rect.x() + g_dual.rect.width() + spacing
        g_right = pylcars.LinearGauge(
            self, QtCore.QRect(right_x, y, dr.width(), h),
            pylcars.Colors.orange, mode="right", title="RAINFALL", right=rain_cfg,
        )
        g_right.set_value("right", 80)

        for g in (g_left, g_dual, g_right):
            g.hide()
        self.frame.pages["GAUGE"]["g_left"]  = g_left
        self.frame.pages["GAUGE"]["g_dual"]  = g_dual
        self.frame.pages["GAUGE"]["g_right"] = g_right

    def _build_split_pill_page(self, dr: QtCore.QRect) -> None:
        SP = pylcars.SplitPillStyles
        MnS = SP.MinorStyle
        MjS = SP.MajorStyle
        Ori = SP.Orientation

        col_gap = 10
        col_w = (dr.width() - col_gap) // 2
        row_h = 50
        row_gap = 8
        pad_v = row_h // 8

        # Left column — MAJOR_RIGHT (minor cap on the left)
        left_col = [
            # label,         key,        value,   numeric, color,                      minor,     major
            ("SOLAR GEN",   "sp_ld_d",  "3842",  3842,   pylcars.Colors.yellow,      MnS.D,     MjS.D),
            ("HOUSE USED",  "sp_lb_d",  "2105",  2105,   pylcars.Colors.flieder,     MnS.BLOCK, MjS.D),
            ("GRID EXPORT", "sp_lr_d",  "1201",  1201,   pylcars.Colors.leuchtblau,  MnS.BAR,   MjS.D),
            ("BATTERY",     "sp_ld_f",  "87",    87,     pylcars.Colors.beige,       MnS.D,     MjS.FLAT),
        ]

        # Right column — MAJOR_LEFT (minor cap on the right)
        right_col = [
            # label,         key,        value,   numeric, color,                      minor,     major
            ("INV OUTPUT",  "sp_rd_f",  "3750",  3750,   pylcars.Colors.hellorange,  MnS.D,     MjS.FLAT),
            ("GRID IMPORT", "sp_rb_f",  "—",     None,   pylcars.Colors.blaugrau,    MnS.BLOCK, MjS.FLAT),
            ("VOLTAGE",     "sp_rr_f",  "230",   230,    pylcars.Colors.orange,      MnS.BAR,   MjS.FLAT),
            ("CURRENT",     "sp_rd_d",  "9",     9,      pylcars.Colors.rot,         MnS.D,     MjS.D),
        ]

        page = self.frame.pages["SPLIT PILLS"]
        col_x_left  = dr.x()
        col_x_right = dr.x() + col_w + col_gap

        for col_x, orientation, col_rows in (
            (col_x_left,  Ori.MAJOR_RIGHT, left_col),
            (col_x_right, Ori.MAJOR_LEFT,  right_col),
        ):
            y = dr.y() + row_gap
            for label, key, value, numeric, pill_color, minor_style, major_style in col_rows:
                pill = pylcars.SplitPill(
                    self,
                    QtCore.QRect(col_x, y, col_w, row_h),
                    label,
                    digit_count=5,
                    pill_color=pill_color,
                    text_color=pylcars.Colors.hellorange,
                    minor_style=minor_style,
                    major_style=major_style,
                    orientation=orientation,
                    top_pad=pad_v,
                    bottom_pad=pad_v,
                )
                pill.set_value(value, numeric)
                pill.hide()
                page[key] = pill
                y += row_h + row_gap

    def _build_info_page(self, dr: QtCore.QRect) -> None:
        texts = [
            "FRAME DEMO",
            "Upper group: ALPHA  BETA  GAMMA",
            "Lower group: INFO  QUIT",
            "Borders: TOP  BOTTOM  LEFT  (C-Style)",
        ]
        for i, text in enumerate(texts):
            lbl = pylcars.Textline(
                self,
                QtCore.QRect(dr.x(), dr.y() + 60 * i, dr.width(), 56),
                pylcars.Colors.beige, 28,
            )
            lbl.setText(text)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.hide()
            self.frame.pages["INFO"][text] = lbl

    def _build_quit_page(self, dr: QtCore.QRect) -> None:
        btn_w, btn_h = 360, 60
        btn_x = dr.x() + (dr.width() - btn_w) // 2
        btn_y = dr.y() + (dr.height() - btn_h) // 2
        quit_btn = pylcars.Bracket(
            self,
            QtCore.QRect(btn_x, btn_y, btn_w, btn_h),
            "QUIT APPLICATION ",
            pylcars.Conditions.alert,
        )
        quit_btn.clicked.connect(QtWidgets.QApplication.quit)
        quit_btn.hide()
        self.frame.pages["QUIT"]["quit_btn"] = quit_btn

    def _quit(self):
        QtWidgets.QApplication.quit()


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = CStyleFrameDemo()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
