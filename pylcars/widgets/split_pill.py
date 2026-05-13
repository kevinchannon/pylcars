"""SplitPill widget — LCARS-style value row with D-bracket, digit value, and pill label.

Layout (left → right, all within the widget rect):

  [left_pad] [D-bracket] [text_pad] [digit value] [text_pad] [pill label] [right_pad]

The D-bracket is the left half of a circle whose diameter equals the inner
height (widget height − top_pad − bottom_pad).  The digit column width is
derived from the pixel width of ``"-" + "8" * digit_count`` at the digit font
size, plus *text_pad* on each side.  The pill fills the remaining horizontal
space.  The same *text_pad* is used as left inset for the pill label text.

Font sizing:
  * Digit value: cap height fills the inner height (via ``points_for_height``).
  * Pill label: ``"small"`` → 40 % of inner height; ``"large"`` → 85 %.
"""
from __future__ import annotations
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from ..colors import Colors
from .. import config
from .frame import points_for_height
from ..color_range import color_for_value


class SplitPill(QtWidgets.QWidget):
    """LCARS-style row: D-bracket on the left, right-aligned digit value, pill label on the right.

    Parameters
    ----------
    parent:
        Parent widget.
    rect:
        Position and size of the widget (includes all padding).
    label:
        Text displayed inside the right pill.
    digit_count:
        Number of digit characters used to calculate the value column width.
        The pixel width is derived from the string ``"-" + "8" * digit_count``.
    text_size:
        ``"small"`` (40 % of inner height, default) or ``"large"`` (85 %).
    pill_color:
        Default background colour for the D-bracket and pill.
    pill_text_color:
        Colour of the label text inside the pill.
    text_color:
        Colour of the digit value text.
    color_ranges:
        Optional list of ``(threshold_or_range, color)`` pairs passed to
        :func:`~pylcars.color_for_value`.  When *numeric* is supplied to
        :meth:`set_value`, the pill colour is looked up here.
    left_pad, right_pad, top_pad, bottom_pad:
        Outer padding in pixels (default 3).
    text_pad:
        Padding on each side of the digit text within the value column, and
        left inset for the pill label (default 3).
    """

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        rect: QtCore.QRect,
        label: str = "",
        digit_count: int = 4,
        text_size: str = "small",
        pill_color: str = Colors.yellow,
        pill_text_color: str = "#000000",
        text_color: str = Colors.hellorange,
        color_ranges: Optional[list] = None,
        left_pad: int = 3,
        right_pad: int = 3,
        top_pad: int = 3,
        bottom_pad: int = 3,
        text_pad: int = 3,
    ) -> None:
        super().__init__(parent)
        self.setGeometry(rect)
        self._label = label
        self._digit_count = digit_count
        self._text_size = text_size
        self._pill_color_hex = pill_color
        self._pill_text_color = QtGui.QColor(pill_text_color)
        self._text_color = QtGui.QColor(text_color)
        self._color_ranges = color_ranges or []
        self._lpad = left_pad
        self._rpad = right_pad
        self._tpad = top_pad
        self._bpad = bottom_pad
        self._txpad = text_pad

        self._value_str = "—"          # em-dash
        self._pill_qcolor = QtGui.QColor(pill_color)

        # Cached layout (invalidated when size changes)
        self._cached_w = -1
        self._cached_h = -1
        self._inner_h = 0
        self._inner_y = 0
        self._radius = 0
        self._digit_col_x = 0
        self._digit_col_w = 0
        self._digit_text_w = 0
        self._pill_x = 0
        self._pill_w = 0
        self._digit_pt = 4
        self._label_pt = 4

        self.show()

    # ── Public API ────────────────────────────────────────────────────────────

    def set_value(self, text: Optional[str], numeric: Optional[float] = None) -> None:
        """Set the displayed value string and optionally drive the pill colour.

        Parameters
        ----------
        text:
            String to display in the digit column.  ``None`` shows an em-dash.
        numeric:
            If provided and *color_ranges* was supplied at construction, the
            pill colour is determined by :func:`~pylcars.color_for_value`.
        """
        self._value_str = text if text is not None else "—"
        if numeric is not None and self._color_ranges:
            self._pill_qcolor = QtGui.QColor(
                color_for_value(numeric, self._color_ranges, self._pill_color_hex)
            )
        else:
            self._pill_qcolor = QtGui.QColor(self._pill_color_hex)
        self.update()

    def set_label(self, label: str) -> None:
        """Update the pill label text."""
        self._label = label
        self.update()

    # ── Internal ──────────────────────────────────────────────────────────────

    def _recompute(self, w: int, h: int) -> None:
        inner_h = max(1, h - self._tpad - self._bpad)
        inner_y = self._tpad
        radius = inner_h // 2

        # Digit font: cap height fills inner_h, minus one point for breathing room
        digit_pt = max(4, points_for_height(config.DEFAULT_FONT_NAME, inner_h) - 1)
        self._digit_pt = digit_pt

        # Label font: fraction of inner_h
        frac = 0.7 if self._text_size == "large" else 0.40
        self._label_pt = points_for_height(config.DEFAULT_FONT_NAME, max(4, int(inner_h * frac)))

        # Digit column width from sample string
        digit_fm = QtGui.QFontMetrics(QtGui.QFont(config.DEFAULT_FONT_NAME, digit_pt))
        digit_text_w = digit_fm.horizontalAdvance("-" + "8" * self._digit_count)

        digit_col_x = self._lpad + radius      # starts right of D-bracket
        digit_col_w = digit_text_w + 2 * self._txpad
        pill_x = digit_col_x + digit_col_w
        pill_w = max(0, w - pill_x - self._rpad)

        self._inner_h = inner_h
        self._inner_y = inner_y
        self._radius = radius
        self._digit_text_w = digit_text_w
        self._digit_col_x = digit_col_x
        self._digit_col_w = digit_col_w
        self._pill_x = pill_x
        self._pill_w = pill_w
        self._cached_w = w
        self._cached_h = h

    @staticmethod
    def _text_y_centre(fm: QtGui.QFontMetrics, inner_y: int, inner_h: int) -> int:
        """Top of font bounding box so that the cap height is centred in inner_h."""
        return inner_y + inner_h // 2 - fm.ascent() + fm.capHeight() // 2

    @staticmethod
    def _text_y_bottom(fm: QtGui.QFontMetrics, inner_y: int, inner_h: int) -> int:
        """Top of font bounding box so that the baseline sits at inner_y + inner_h."""
        return inner_y + inner_h - fm.ascent()

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()

        if w != self._cached_w or h != self._cached_h:
            self._recompute(w, h)

        ih = self._inner_h
        iy = self._inner_y
        r  = self._radius

        # ── D-bracket: left half of a circle of diameter ih ──────────────────
        p.save()
        p.setClipRect(QtCore.QRect(self._lpad, iy, r, ih))
        p.setBrush(QtGui.QBrush(self._pill_qcolor))
        p.setPen(QtCore.Qt.NoPen)
        p.drawEllipse(QtCore.QRectF(self._lpad, iy, ih, ih))
        p.restore()

        # ── Digit value: left-aligned, baseline at inner bottom ──────────────
        digit_font = QtGui.QFont(config.DEFAULT_FONT_NAME, self._digit_pt)
        digit_fm   = QtGui.QFontMetrics(digit_font)
        p.setFont(digit_font)
        p.setPen(self._text_color)
        p.drawText(
            QtCore.QRect(
                self._digit_col_x + self._txpad,
                self._text_y_bottom(digit_fm, iy, ih),
                self._digit_text_w,
                digit_fm.height(),
            ),
            QtCore.Qt.AlignRight | QtCore.Qt.AlignTop,
            self._value_str,
        )

        # ── Pill: rectangle body + D-shaped right cap ─────────────────────────
        px, pw = self._pill_x, self._pill_w
        if pw > 0:
            p.setPen(QtCore.Qt.NoPen)
            p.setBrush(QtGui.QBrush(self._pill_qcolor))
            p.drawRect(QtCore.QRectF(px, iy, pw - r, ih))
            p.save()
            p.setClipRect(QtCore.QRectF(px + pw - r, iy, r + 1, ih))
            p.drawEllipse(QtCore.QRectF(px + pw - ih, iy, ih, ih))
            p.restore()

            # ── Pill label: small → bottom-left; large → cap-height centred ────
            if self._label:
                label_font = QtGui.QFont(config.DEFAULT_FONT_NAME, self._label_pt)
                label_fm   = QtGui.QFontMetrics(label_font)
                label_x = px + self._txpad
                label_w = pw - self._txpad - r
                p.setFont(label_font)
                p.setPen(self._pill_text_color)
                if self._text_size == "large":
                    label_y = self._text_y_centre(label_fm, iy, ih)
                else:
                    label_y = self._text_y_bottom(label_fm, iy, ih) - self._txpad
                p.drawText(
                    QtCore.QRect(label_x, label_y, label_w, label_fm.height()),
                    QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop,
                    self._label,
                )

        p.end()
