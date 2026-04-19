# -*- coding: utf-8 -*-
"""C-Style (TBL) frame demo.

Demonstrates Frame with borders={TOP, BOTTOM, LEFT} — the classic C-Style.

Run with:
    python -m pylcars.demos.c_style_frame_demo
"""
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
            left_upper_buttons=["ALPHA", "BETA", "GAMMA"],
            left_lower_buttons=["INFO", "QUIT"],
            header_text="C-STYLE",
            footer_text="DEMO",
            color=pylcars.Colors.orange,
            color_active=pylcars.Colors.leuchtblau,
        )

        dr = self.frame.display_rect()

        self._build_page("ALPHA", pylcars.Colors.orange,     "ALPHA")
        self._build_page("BETA",  pylcars.Colors.flieder,    "BETA")
        self._build_page("GAMMA", pylcars.Colors.leuchtblau, "GAMMA")
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
