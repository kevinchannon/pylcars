# -*- coding: utf-8 -*-
"""S-Style frame demo.

Demonstrates SFrame (mirror=False) with independent upper/lower page switching,
optional top/bottom bars, and a title on the mid-bar.

Run with:
    python -m pylcars.demos.s_frame_demo
"""
import sys
from PyQt5 import QtCore, QtWidgets

import pylcars


class SFrameDemo(pylcars.Lcars):

    def __init__(self, parent=None):
        pylcars.Lcars.__init__(self, parent)

        self.frame = pylcars.SFrame(
            self,
            QtCore.QRect(0, 0, 800, 480),
            mirror=False,
            upper_buttons=["ALPHA", "BETA"],
            lower_buttons=["INFO", "QUIT"],
            split=0.5,
            has_top=False,
            has_bottom=True,
            title="S-STYLE",
            header_text="DEMO",
            footer_text="PYLCARS",
            color=pylcars.Colors.flieder,
            color_active=pylcars.Colors.leuchtblau,
        )

        udr = self.frame.upper_display_rect()
        ldr = self.frame.lower_display_rect()

        pylcars.Block(self, udr, pylcars.Colors.blaugrau)
        pylcars.Block(self, ldr, pylcars.Colors.rostbraun)

        self._build_upper_page("ALPHA", pylcars.Colors.flieder,    "ALPHA", udr)
        self._build_upper_page("BETA",  pylcars.Colors.leuchtblau, "BETA",  udr)
        self._build_lower_info_page(ldr)
        self._build_lower_quit_page(ldr)

        self.frame.upper_blend_in(self.frame.upper_active_page)
        self.frame.lower_blend_in(self.frame.lower_active_page)

    def _build_upper_page(self, name: str, color: str, label: str,
                          udr: QtCore.QRect) -> None:
        lbl = pylcars.Textline(self, udr, color, 48)
        lbl.setText(label)
        lbl.setAlignment(QtCore.Qt.AlignCenter)
        lbl.hide()
        self.frame.upper_pages[name]["label"] = lbl

    def _build_lower_info_page(self, ldr: QtCore.QRect) -> None:
        texts = [
            "S-FRAME DEMO",
            "Upper buttons: ALPHA  BETA",
            "Lower buttons: INFO  QUIT",
        ]
        for i, text in enumerate(texts):
            lbl = pylcars.Textline(
                self,
                QtCore.QRect(ldr.x(), ldr.y() + 50 * i, ldr.width(), 44),
                pylcars.Colors.beige, 22,
            )
            lbl.setText(text)
            lbl.setAlignment(QtCore.Qt.AlignCenter)
            lbl.hide()
            self.frame.lower_pages["INFO"][f"line{i}"] = lbl

    def _build_lower_quit_page(self, ldr: QtCore.QRect) -> None:
        btn_w, btn_h = 320, 56
        btn_x = ldr.x() + (ldr.width() - btn_w) // 2
        btn_y = ldr.y() + (ldr.height() - btn_h) // 2
        btn = pylcars.Bracket(
            self,
            QtCore.QRect(btn_x, btn_y, btn_w, btn_h),
            "QUIT APPLICATION ",
            pylcars.Conditions.alert,
        )
        btn.clicked.connect(QtWidgets.QApplication.quit)
        btn.hide()
        self.frame.lower_pages["QUIT"]["btn"] = btn


def main():
    app = QtWidgets.QApplication(sys.argv)
    form = SFrameDemo()
    form.show()
    app.exec_()


if __name__ == "__main__":
    main()
