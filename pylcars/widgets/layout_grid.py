from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from ..colors import Colors
from .block import Block
from .deco import Deco
from .textline import Textline


class LayoutGrid:
    COLS = 6
    ROWS = 6
    TITLE_BAR_HEIGHT = 30
    TITLE_FONT_SIZE = 36
    PADDING = 5

    def __init__(
        self,
        lcars: QtWidgets.QWidget,
        rect: QtCore.QRect,
        title: Optional[str] = None,
        color: str = Colors.orange,
    ) -> None:
        if title:
            self._render_title_bar(lcars, rect, title, color)
            self._content_rect = QtCore.QRect(
                rect.x(),
                rect.y() + self.TITLE_BAR_HEIGHT,
                rect.width(),
                rect.height() - self.TITLE_BAR_HEIGHT,
            )
        else:
            self._content_rect = rect

    def _render_title_bar(
        self,
        lcars: QtWidgets.QWidget,
        rect: QtCore.QRect,
        title: str,
        color: str,
    ) -> None:
        bar_h = self.TITLE_BAR_HEIGHT
        Block(lcars, QtCore.QRect(rect.x(), rect.y(), rect.width(), bar_h), color)

        cap_w = bar_h
        r = bar_h / 2

        right_cap_svg = (
            f'<svg height="{bar_h}" width="{cap_w}">'
            f'<rect x="0" y="0" width="{r}" height="{bar_h}" fill="{{c}}" />'
            f'<circle cx="{r}" cy="{r}" r="{r}" fill="{{c}}" />'
            f'</svg>'
        )
        cap_x = rect.x() + rect.width() - cap_w
        Deco(lcars, QtCore.QRect(cap_x, rect.y(), cap_w, bar_h), color, svg=right_cap_svg)

        left_cap_svg = (
            f'<svg height="{bar_h}" width="{cap_w}">'
            f'<rect x="{r}" y="0" width="{r}" height="{bar_h}" fill="{{c}}" />'
            f'<circle cx="{r}" cy="{r}" r="{r}" fill="{{c}}" />'
            f'</svg>'
        )
        Deco(lcars, QtCore.QRect(rect.x(), rect.y(), cap_w, bar_h), color, svg=left_cap_svg)

        title_gap = 12
        cutout_w = QtGui.QFontMetrics(QtGui.QFont("LCARS", self.TITLE_FONT_SIZE)).horizontalAdvance(title) + 16
        cutout_x = cap_x - title_gap - cutout_w
        cutout_rect = QtCore.QRect(cutout_x, rect.y(), cutout_w, bar_h)
        Block(lcars, cutout_rect, "#000000")
        label = Textline(lcars, cutout_rect, color, self.TITLE_FONT_SIZE)
        label.setText(title)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)

    def cell_rect(self, row: int, col: int, width_cells: int, height_cells: int) -> QtCore.QRect:
        cw = self._content_rect.width() / self.COLS
        ch = self._content_rect.height() / self.ROWS
        x = self._content_rect.x() + int(col * cw)
        y = self._content_rect.y() + int(row * ch)
        w = int((col + width_cells) * cw) - int(col * cw)
        h = int((row + height_cells) * ch) - int(row * ch)
        p = self.PADDING
        return QtCore.QRect(x + p, y + p, w - 2 * p, h - 2 * p)
