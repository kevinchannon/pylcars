# -*- coding: utf-8 -*-
"""LCARS-style vertical linear gauge widget."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets

from ..colors import Colors
from .widgets import Widgets


@dataclass
class ZoneInterval:
    """Visual style of a gauge axis segment starting at *start*."""
    start: float
    colour: str = Colors.orange
    thickness: int = 5


@dataclass
class GaugeConfig:
    """Configuration for one side (left or right) of a LinearGauge."""
    range: Tuple[float, float]   # (min, max)
    interval: float              # tick spacing
    title: str = ""
    unit: str = ""
    marker_size: int = 25        # triangle height in px
    zones: List[ZoneInterval] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _fmt_value(v: float) -> str:
    return str(int(v)) if v == int(v) else f"{v:.1f}"


def _points_for_height(family: str, target_px: int) -> int:
    """Largest point size whose cap height does not exceed *target_px*.

    Binary-search implementation identical to frame.py's ``points_for_height``.
    """
    lo, hi = 6, 200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if QtGui.QFontMetrics(QtGui.QFont(family, mid)).capHeight() <= target_px:
            lo = mid
        else:
            hi = mid - 1
    return lo


def _badge_path(x: int, y: int, w: int, h: int, cap: str) -> QtGui.QPainterPath:
    """Pill with a flat edge on one side and a semicircular cap on the other.

    *cap* = ``"left"`` → semicircle on left, flat on right.
    *cap* = ``"right"`` → flat on left, semicircle on right.
    """
    r = h / 2
    path = QtGui.QPainterPath()
    if cap == "left":
        path.moveTo(x + w, y)
        path.lineTo(x + r, y)
        path.arcTo(x, y, h, h, 90, 180)       # top → left semicircle → bottom
        path.lineTo(x + w, y + h)
        path.closeSubpath()
    else:
        path.moveTo(x, y)
        path.lineTo(x + w - r, y)
        path.arcTo(x + w - h, y, h, h, 90, -180)  # top → right semicircle → bottom
        path.lineTo(x, y + h)
        path.closeSubpath()
    return path


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------

class LinearGauge(Widgets, QtWidgets.QWidget):
    """LCARS-style dual vertical linear gauge.

    *mode* is ``"left"``, ``"right"``, or ``"dual"``.  Pass *left* / *right*
    as :class:`GaugeConfig` instances.  The widget auto-sizes its width to
    the minimum needed to fit all content.

    Usage::

        cfg = GaugeConfig(
            range=(0, 100), interval=10, title="TEMP", unit="°C",
            marker_size=28,
            zones=[ZoneInterval(0, pylcars.Colors.leuchtblau),
                   ZoneInterval(70, pylcars.Colors.hellorange),
                   ZoneInterval(90, pylcars.Colors.rot)],
        )
        g = pylcars.LinearGauge(self, rect, pylcars.Colors.orange,
                                mode="left", title="CURRENT", left=cfg)
        g.set_value("left", 75)
    """

    _AXIS_GAP = 10      # px gap between left and right axes in dual mode
    _TICK_LEN = 8       # px length of each tick mark
    _ELEM_GAP = 6       # px gap between marker / value / badge elements
    _BRACKET_ARM = 15   # px horizontal arm length of gauge end-bracket
    _BRACKET_LEG = 10   # px vertical leg length of gauge end-bracket
    _BRACKET_W = 3      # px line width of gauge end-bracket

    def __init__(
        self,
        lcars: QtWidgets.QWidget,
        rect: QtCore.QRect,
        color: str,
        *,
        mode: str = "dual",
        title: str = "",
        left: Optional[GaugeConfig] = None,
        right: Optional[GaugeConfig] = None,
    ) -> None:
        # Widgets.__init__ sets self.default_font — must come first
        Widgets.__init__(self, lcars)
        self.color = color
        self.mode = mode
        self.title = title
        self.left_config = left
        self.right_config = right
        self._values: Dict[str, Optional[float]] = {"left": None, "right": None}

        # Auto-compute width from content; axes stored as absolute x coordinates
        total_w, self._left_ax, self._right_ax = self._compute_layout()

        QtWidgets.QWidget.__init__(self, lcars)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        computed_rect = QtCore.QRect(rect.x(), rect.y(), total_w, rect.height())
        self.setGeometry(computed_rect)
        self.rect = computed_rect
        self.show()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_value(self, side: str, value: float) -> None:
        """Set the current reading for ``"left"`` or ``"right"``."""
        self._values[side] = value
        self.update()

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _side_content_width(self, config: GaugeConfig) -> int:
        """Horizontal pixels required between the gauge axis and the outer edge."""
        family = self.default_font.family()
        marker_h = config.marker_size
        marker_w = marker_h // 2

        val_pt = _points_for_height(family, marker_h - 2)
        val_fm = QtGui.QFontMetrics(QtGui.QFont(family, val_pt))
        tick_fm = QtGui.QFontMetrics(self.default_font)

        # Widest tick label over the full range
        max_lw, v = 0, config.range[0]
        while v <= config.range[1] + 1e-9:
            max_lw = max(max_lw, tick_fm.horizontalAdvance(_fmt_value(v)))
            v = round(v + config.interval, 10)

        # Widest possible value text
        max_val_w = max(
            val_fm.horizontalAdvance(_fmt_value(config.range[0])),
            val_fm.horizontalAdvance(_fmt_value(config.range[1])),
        )

        # Badge geometry — height always equals marker height
        badge_h = marker_h
        unit_font_layout = QtGui.QFont(self.default_font)
        unit_font_layout.setPointSize(self.default_font.pointSize() + 2)
        unit_fm = QtGui.QFontMetrics(unit_font_layout)
        badge_full_w = unit_fm.horizontalAdvance(config.unit) + 10 + badge_h // 2

        tick_area   = self._TICK_LEN + max_lw + 3
        # Marker sits beyond the tick labels, so its offset from the axis equals tick_area
        marker_area = tick_area + self._ELEM_GAP + marker_w + self._ELEM_GAP + max_val_w + self._ELEM_GAP + badge_full_w + self._ELEM_GAP

        return marker_area

    def _compute_layout(self) -> Tuple[int, Optional[int], Optional[int]]:
        """Return ``(total_width, left_axis_x, right_axis_x)``."""
        pad = 20  # outer margin for single-gauge modes

        lw = self._side_content_width(self.left_config)  if self.left_config  and self.mode in ("left",  "dual") else 0
        rw = self._side_content_width(self.right_config) if self.right_config and self.mode in ("right", "dual") else 0

        if self.mode == "dual":
            return lw + self._AXIS_GAP + rw, lw, lw + self._AXIS_GAP
        if self.mode == "left":
            return lw + pad, lw, None
        # right
        return pad + rw, None, pad

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _zone_at(config: GaugeConfig, value: float) -> ZoneInterval:
        if not config.zones:
            return ZoneInterval(start=config.range[0])
        active = config.zones[0]
        for z in sorted(config.zones, key=lambda z: z.start):
            if z.start <= value:
                active = z
        return active

    @staticmethod
    def _val_to_y(v: float, vmin: float, vmax: float, top: int, bottom: int) -> int:
        frac = (v - vmin) / (vmax - vmin) if vmax != vmin else 0.0
        return bottom - int(frac * (bottom - top))

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        p = QtGui.QPainter(self)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QtGui.QColor("#000000"))

        title_font = QtGui.QFont(self.default_font)
        title_font.setPointSize(self.default_font.pointSize() + 4)
        gtitle_font = QtGui.QFont(self.default_font)
        tick_font   = QtGui.QFont(self.default_font)

        title_fm  = QtGui.QFontMetrics(title_font)
        gtitle_fm = QtGui.QFontMetrics(gtitle_font)

        title_h   = title_fm.height() + 10
        bottom_h  = gtitle_fm.height() + 10
        gauge_top    = title_h + 6
        gauge_bottom = h - bottom_h - 6

        # Title — text only, no background fill.
        # Dual: centred on the midpoint between the two axes.
        # Left-only: right-aligned to the axis.
        # Right-only: left-aligned from the axis.
        p.setFont(title_font)
        p.setPen(QtGui.QColor(self.color))
        title_lw = title_fm.horizontalAdvance(self.title)
        title_ly = (title_h - title_fm.height()) // 2 + title_fm.ascent()
        if self.mode == "dual" and self._left_ax is not None and self._right_ax is not None:
            title_lx = (self._left_ax + self._right_ax) // 2 - title_lw // 2
        elif self.mode == "left" and self._left_ax is not None:
            title_lx = self._left_ax - title_lw
        elif self.mode == "right" and self._right_ax is not None:
            title_lx = self._right_ax
        else:
            title_lx = (w - title_lw) // 2
        p.drawText(title_lx, title_ly, self.title)

        # Gauges
        if self._left_ax is not None and self.left_config:
            self._draw_gauge(p, self._left_ax, gauge_top, gauge_bottom,
                             self.left_config, self._values["left"], "left", tick_font)
        if self._right_ax is not None and self.right_config:
            self._draw_gauge(p, self._right_ax, gauge_top, gauge_bottom,
                             self.right_config, self._values["right"], "right", tick_font)

        # Bottom gauge titles — left right-aligned, right left-aligned
        p.setFont(gtitle_font)
        p.setPen(QtGui.QColor(self.color))
        ty = h - gtitle_fm.height() - 4
        th = gtitle_fm.height() + 4

        if self.mode in ("left", "dual") and self.left_config and self._left_ax is not None:
            p.drawText(QtCore.QRect(0, ty, self._left_ax, th),
                       QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter,
                       self.left_config.title)

        if self.mode in ("right", "dual") and self.right_config and self._right_ax is not None:
            p.drawText(QtCore.QRect(self._right_ax, ty, w - self._right_ax, th),
                       QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter,
                       self.right_config.title)

        p.end()

    def _draw_gauge(
        self,
        p: QtGui.QPainter,
        axis_x: int,
        top: int,
        bottom: int,
        config: GaugeConfig,
        value: Optional[float],
        side: str,
        tick_font: QtGui.QFont,
    ) -> None:
        vmin, vmax = config.range
        tick_fm = QtGui.QFontMetrics(tick_font)
        sign = -1 if side == "left" else 1

        # Zone bars
        zones = sorted(config.zones, key=lambda z: z.start) if config.zones else []
        if not zones:
            zones = [ZoneInterval(start=vmin)]
        for i, zone in enumerate(zones):
            z_start = max(zone.start, vmin)
            z_end   = min(zones[i + 1].start if i + 1 < len(zones) else vmax, vmax)
            if z_end <= z_start:
                continue
            y_bot = self._val_to_y(z_start, vmin, vmax, top, bottom)
            y_top = self._val_to_y(z_end,   vmin, vmax, top, bottom)
            bar_h = y_bot - y_top
            if bar_h <= 0:
                continue
            half_t = zone.thickness // 2
            p.fillRect(axis_x - half_t, y_top, zone.thickness, bar_h,
                       QtGui.QColor(zone.colour))

        # L-shaped end brackets at top and bottom of the gauge axis
        bracket_pen = QtGui.QPen(QtGui.QColor(self.color), self._BRACKET_W)
        bracket_pen.setCapStyle(QtCore.Qt.SquareCap)
        p.setPen(bracket_pen)
        outer_x = axis_x + sign * self._BRACKET_ARM
        p.drawLine(axis_x, top,    outer_x, top)               # top arm
        p.drawLine(outer_x, top,   outer_x, top + self._BRACKET_LEG)   # top leg (down)
        p.drawLine(axis_x, bottom, outer_x, bottom)            # bottom arm
        p.drawLine(outer_x, bottom, outer_x, bottom - self._BRACKET_LEG)  # bottom leg (up)

        # Tick marks and labels — track widest label for marker offset
        p.setFont(tick_font)
        max_tick_lw = 0
        v = vmin
        while v <= vmax + 1e-9:
            y = self._val_to_y(v, vmin, vmax, top, bottom)
            p.setPen(QtGui.QPen(QtGui.QColor("#cccccc"), 1))
            p.drawLine(axis_x, y, axis_x + sign * self._TICK_LEN, y)
            label = _fmt_value(v)
            lw = tick_fm.horizontalAdvance(label)
            max_tick_lw = max(max_tick_lw, lw)
            lx = (axis_x - self._TICK_LEN - lw - 3) if side == "left" else (axis_x + self._TICK_LEN + 3)
            p.setPen(QtGui.QColor("#fc9"))
            p.drawText(lx, y + tick_fm.ascent() // 2, label)
            v = round(v + config.interval, 10)

        if value is None or not (vmin <= value <= vmax):
            return

        zone     = self._zone_at(config, value)
        zone_col = QtGui.QColor(zone.colour)
        marker_y = self._val_to_y(value, vmin, vmax, top, bottom)

        # Value font: cap height = marker height (use same binary-search as frame.py)
        marker_h = config.marker_size
        val_pt   = _points_for_height(self.default_font.family(), marker_h - 2)
        val_font = QtGui.QFont(self.default_font.family(), val_pt)
        val_fm   = QtGui.QFontMetrics(val_font)

        marker_w = marker_h // 2   # triangle width = half its height
        half_mh  = marker_h // 2

        # Offset marker apex past the tick labels so the marker never obscures them
        tick_clearance = self._TICK_LEN + max_tick_lw + self._ELEM_GAP
        if side == "left":
            apex_x = axis_x - tick_clearance
            base_x = apex_x - marker_w
        else:
            apex_x = axis_x + tick_clearance
            base_x = apex_x + marker_w

        # Marker triangle
        tri = [QtCore.QPoint(apex_x, marker_y),
               QtCore.QPoint(base_x, marker_y - half_mh),
               QtCore.QPoint(base_x, marker_y + half_mh)]
        p.setBrush(QtGui.QBrush(zone_col))
        p.setPen(QtCore.Qt.NoPen)
        p.drawPolygon(*tri)

        # Current value text
        val_text = _fmt_value(value)
        val_w    = val_fm.horizontalAdvance(val_text)
        p.setFont(val_font)
        p.setPen(zone_col)
        if side == "left":
            val_x = base_x - val_w - self._ELEM_GAP
        else:
            val_x = base_x + self._ELEM_GAP
        p.drawText(val_x, marker_y - val_fm.height() // 2 + val_fm.ascent(), val_text)

        # Unit badge — pill height = marker height; font scaled to fit inside
        badge_h = marker_h
        badge_r = badge_h // 2
        unit_font = QtGui.QFont(self.default_font)
        unit_font.setPointSize(self.default_font.pointSize() + 2)
        unit_fm  = QtGui.QFontMetrics(unit_font)
        unit_w   = unit_fm.horizontalAdvance(config.unit)
        badge_full_w = unit_w + 10 + badge_r   # 10 = 2 × 5 px horizontal pad
        badge_y  = marker_y - badge_h // 2

        if side == "left":
            badge_x = val_x - badge_full_w - self._ELEM_GAP
            cap = "left"
        else:
            badge_x = val_x + val_w + self._ELEM_GAP
            cap = "right"

        p.setBrush(QtGui.QBrush(zone_col))
        p.setPen(QtCore.Qt.NoPen)
        p.drawPath(_badge_path(badge_x, badge_y, badge_full_w, badge_h, cap))

        p.setPen(QtGui.QColor("#000000"))
        p.setFont(unit_font)
        p.drawText(QtCore.QRect(badge_x, badge_y, badge_full_w, badge_h),
                   QtCore.Qt.AlignCenter, config.unit)
