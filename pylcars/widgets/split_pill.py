"""SplitPill widget — LCARS-style value row with D-bracket, digit value, and pill label.

Layout (left → right, MAJOR_RIGHT orientation):

  [left_pad] [minor cap] [text_pad] [digit value] [text_pad] [major pill] [right_pad]

Layout (left → right, MAJOR_LEFT orientation):

  [left_pad] [major pill] [text_pad] [digit value] [text_pad] [minor cap] [right_pad]

The minor cap shape is controlled by ``SplitPillStyles.MinorStyle``:
  * ``D`` — left (or right) half of a circle whose diameter equals the inner height.
  * ``BLOCK`` — same width as D but drawn as a rectangle.
  * ``BAR`` — a narrow vertical bar (≈ ⅓ of the D radius).

The major pill end-cap is controlled by ``SplitPillStyles.MajorStyle``:
  * ``D`` — rectangle body with a D-shaped (half-circle) far-end cap.
  * ``FLAT`` — rectangle body with a flat far end.

Orientation is controlled by ``SplitPillStyles.Orientation``:
  * ``MAJOR_RIGHT`` — minor cap on left, major pill on right (default).
  * ``MAJOR_LEFT``  — major pill on left, minor cap on right (mirrored).

Font sizing:
  * Digit value: cap height fills the inner height (via ``points_for_height``).
  * Pill label: ``"small"`` → 40 % of inner height; ``"large"`` → 70 %.
"""
from __future__ import annotations
from typing import Optional
from enum import Enum

from PyQt5 import QtCore, QtGui, QtWidgets

from ..colors import Colors
from .. import config
from .frame import points_for_height
from ..color_range import color_for_value


class SplitPillStyles:
    class MinorStyle(Enum):
        D = 0
        BLOCK = 1
        BAR = 2

    class MajorStyle(Enum):
        D = 0
        FLAT = 1

    class Orientation(Enum):
        MAJOR_RIGHT = 0
        MAJOR_LEFT = 1


class SplitPill(QtWidgets.QWidget):
    """LCARS-style row: minor cap, digit value, major pill.

    Parameters
    ----------
    parent:
        Parent widget.
    rect:
        Position and size of the widget (includes all padding).
    label:
        Text displayed inside the major pill.
    digit_count:
        Number of digit characters used to calculate the value column width.
        The pixel width is derived from the string ``"-" + "8" * digit_count``.
    text_size:
        ``"small"`` (40 % of inner height, default) or ``"large"`` (70 %).
    pill_color:
        Default background colour for the minor cap and major pill.
    pill_text_color:
        Colour of the label text inside the major pill.
    text_color:
        Colour of the digit value text.
    color_ranges:
        Optional list of ``(threshold_or_range, color)`` pairs passed to
        :func:`~pylcars.color_for_value`.  When *numeric* is supplied to
        :meth:`set_value`, the pill colour is looked up here.
    minor_style:
        Shape of the small cap (``D``, ``BLOCK``, or ``BAR``).
    major_style:
        End-cap style of the large pill (``D`` or ``FLAT``).
    orientation:
        Whether the major pill is on the right (``MAJOR_RIGHT``) or left
        (``MAJOR_LEFT``).
    left_pad, right_pad, top_pad, bottom_pad:
        Outer padding in pixels (default 3).
    text_pad:
        Padding on each side of the digit text within the value column, and
        inset for the pill label (default 3).
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
        minor_style: SplitPillStyles.MinorStyle = SplitPillStyles.MinorStyle.D,
        major_style: SplitPillStyles.MajorStyle = SplitPillStyles.MajorStyle.D,
        orientation: SplitPillStyles.Orientation = SplitPillStyles.Orientation.MAJOR_RIGHT,
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
        self._minor_style = minor_style
        self._major_style = major_style
        self._orientation = orientation
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
        self._minor_x = 0
        self._minor_slot = 0   # layout slot width (always radius)
        self._bar_w = 0        # actual drawn width for BAR style
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

        digit_pt = max(4, points_for_height(config.DEFAULT_FONT_NAME, inner_h) - 1)
        self._digit_pt = digit_pt

        frac = 0.7 if self._text_size == "large" else 0.40
        self._label_pt = points_for_height(config.DEFAULT_FONT_NAME, max(4, int(inner_h * frac)))

        digit_fm = QtGui.QFontMetrics(QtGui.QFont(config.DEFAULT_FONT_NAME, digit_pt))
        digit_text_w = digit_fm.horizontalAdvance("-" + "8" * self._digit_count)
        digit_col_w = digit_text_w + 2 * self._txpad

        # The minor cap always occupies a slot of width `radius` in the layout so
        # that the digit column starts at the same x regardless of minor style.
        # BAR draws narrower within that slot; the slack becomes visual padding.
        minor_slot = radius
        bar_w = max(3, radius // 3)

        if self._orientation == SplitPillStyles.Orientation.MAJOR_RIGHT:
            minor_x = self._lpad
            digit_col_x = minor_x + minor_slot
            pill_x = digit_col_x + digit_col_w
            pill_w = max(0, w - pill_x - self._rpad)
        else:  # MAJOR_LEFT
            minor_x = w - self._rpad - minor_slot
            digit_col_x = minor_x - digit_col_w
            pill_x = self._lpad
            pill_w = max(0, digit_col_x - self._lpad)

        self._inner_h = inner_h
        self._inner_y = inner_y
        self._radius = radius
        self._minor_x = minor_x
        self._minor_slot = minor_slot
        self._bar_w = bar_w
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

    def _draw_minor_cap(self, p: QtGui.QPainter) -> None:
        ih = self._inner_h
        iy = self._inner_y
        r  = self._radius
        mx = self._minor_x
        major_right = self._orientation == SplitPillStyles.Orientation.MAJOR_RIGHT

        p.save()
        p.setBrush(QtGui.QBrush(self._pill_qcolor))
        p.setPen(QtCore.Qt.NoPen)

        if self._minor_style == SplitPillStyles.MinorStyle.D:
            if major_right:
                # Left half of circle: flat on right, curve on left
                p.setClipRect(QtCore.QRect(mx, iy, r, ih))
                p.drawEllipse(QtCore.QRectF(mx, iy, ih, ih))
            else:
                # Right half of circle: flat on left, curve on right
                p.setClipRect(QtCore.QRect(mx, iy, r + 1, ih))
                p.drawEllipse(QtCore.QRectF(mx - r, iy, ih, ih))
        elif self._minor_style == SplitPillStyles.MinorStyle.BLOCK:
            p.drawRect(QtCore.QRectF(mx, iy, r, ih))
        else:  # BAR
            bw = self._bar_w
            # Bar sits at the outer edge of the slot (left for MAJOR_RIGHT, right for MAJOR_LEFT)
            bx = mx if major_right else mx + r - bw
            p.drawRect(QtCore.QRectF(bx, iy, bw, ih))

        p.restore()

    def _draw_major_pill(self, p: QtGui.QPainter) -> None:
        ih = self._inner_h
        iy = self._inner_y
        r  = self._radius
        px = self._pill_x
        pw = self._pill_w

        if pw <= 0:
            return

        p.setPen(QtCore.Qt.NoPen)
        p.setBrush(QtGui.QBrush(self._pill_qcolor))

        major_right = self._orientation == SplitPillStyles.Orientation.MAJOR_RIGHT

        if self._major_style == SplitPillStyles.MajorStyle.D:
            if major_right:
                # Body + right D-cap
                p.drawRect(QtCore.QRectF(px, iy, pw - r, ih))
                p.save()
                p.setClipRect(QtCore.QRectF(px + pw - r, iy, r + 1, ih))
                p.drawEllipse(QtCore.QRectF(px + pw - ih, iy, ih, ih))
                p.restore()
            else:
                # Left D-cap + body
                p.save()
                p.setClipRect(QtCore.QRectF(px, iy, r + 1, ih))
                p.drawEllipse(QtCore.QRectF(px, iy, ih, ih))
                p.restore()
                p.drawRect(QtCore.QRectF(px + r, iy, pw - r, ih))
        else:  # FLAT
            p.drawRect(QtCore.QRectF(px, iy, pw, ih))

    def _draw_pill_label(self, p: QtGui.QPainter) -> None:
        if not self._label:
            return

        ih = self._inner_h
        iy = self._inner_y
        r  = self._radius
        px = self._pill_x
        pw = self._pill_w

        if pw <= 0:
            return

        label_font = QtGui.QFont(config.DEFAULT_FONT_NAME, self._label_pt)
        label_fm   = QtGui.QFontMetrics(label_font)
        p.setFont(label_font)
        p.setPen(self._pill_text_color)

        major_right = self._orientation == SplitPillStyles.Orientation.MAJOR_RIGHT
        has_d_cap = self._major_style == SplitPillStyles.MajorStyle.D

        if major_right:
            label_x = px + self._txpad
            label_w = pw - self._txpad - (r if has_d_cap else 0)
        else:
            label_x = px + (r if has_d_cap else 0) + self._txpad
            label_w = pw - (r if has_d_cap else 0) - self._txpad

        if self._text_size == "large":
            label_y = self._text_y_centre(label_fm, iy, ih)
        else:
            label_y = self._text_y_bottom(label_fm, iy, ih) - self._txpad

        p.drawText(
            QtCore.QRect(label_x, label_y, max(0, label_w), label_fm.height()),
            QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop,
            self._label,
        )

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing)
        w, h = self.width(), self.height()

        if w != self._cached_w or h != self._cached_h:
            self._recompute(w, h)

        ih = self._inner_h
        iy = self._inner_y

        self._draw_minor_cap(p)

        # ── Digit value: right-aligned, baseline at inner bottom ─────────────
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

        self._draw_major_pill(p)
        self._draw_pill_label(p)

        p.end()
