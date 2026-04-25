# -*- coding: utf-8 -*-
"""LCARS-style XY line plot widget."""
import math
from typing import List, Optional, Tuple

from PyQt5 import QtCore, QtGui, QtWidgets

from .widgets import Widgets

_Series = Tuple[List[float], List[float]]

# Auto-assigned series colours — light grey first, orange reserved for last
_SERIES_COLORS = [
    "#ffffff",  # white
    "#aaaaaa",  # very light grey
    "#99c",     # blaugrau
    "#99f",     # leuchtblau
    "#fc4",     # hellorange (light orange)
    "#f90",     # orange
]


def _nice_ticks(vmin: float, vmax: float, n: int = 5) -> List[float]:
    span = vmax - vmin
    if span == 0:
        return [vmin]
    step = span / n
    mag = 10 ** math.floor(math.log10(step))
    r = step / mag
    if r < 1.5:
        nice = mag
    elif r < 3.5:
        nice = 2 * mag
    elif r < 7.5:
        nice = 5 * mag
    else:
        nice = 10 * mag
    first = math.ceil(vmin / nice) * nice
    ticks: List[float] = []
    t = first
    while t <= vmax + nice * 1e-6:
        ticks.append(round(t, 10))
        t += nice
    return ticks


def _log_ticks(vmin: float, vmax: float) -> List[float]:
    if vmin <= 0:
        vmin = 1e-300
    lo = math.floor(math.log10(vmin))
    hi = math.ceil(math.log10(vmax))
    return [10.0 ** e for e in range(int(lo), int(hi) + 1)]


def _fmt_tick(v: float) -> str:
    if v == 0:
        return "0"
    s = f"{v:.3g}"
    if "e" in s:
        m, e = s.split("e")
        return f"{m}e{int(e)}"
    return s


class Plot(Widgets, QtWidgets.QWidget):
    """LCARS-style XY line plot with optional gridlines and log-scale axes.

    Supports multiple data series, each rendered as a thick coloured line on a
    black background with blaugrau axes and beige tick labels.

    Usage::

        plot = pylcars.Plot(self, rect, pylcars.Colors.leuchtblau, grid=True)
        plot.set_data(([0, 1, 2, 3], [0, 1, 4, 9]))
        plot.add_series(([0, 1, 2, 3], [3, 2, 1, 0]), color=pylcars.Colors.orange)
    """

    _MR = 15   # right margin (fixed)
    _MT = 15   # top margin (fixed)

    def __init__(
        self,
        lcars: QtWidgets.QWidget,
        rect: QtCore.QRect,
        color: str,
        *,
        grid: bool = True,
        log_x: bool = False,
        log_y: bool = False,
        line_width: int = 5,
    ) -> None:
        Widgets.__init__(self, lcars)
        QtWidgets.QWidget.__init__(self, lcars)
        self.setAttribute(QtCore.Qt.WA_OpaquePaintEvent)
        self.setGeometry(rect)
        self.rect = rect
        self.color = color
        self.grid = grid
        self.log_x = log_x
        self.log_y = log_y
        self.line_width = line_width
        self._series: List[Tuple[List[float], List[float], str]] = []
        self._auto_color_idx: int = 0
        self.show()

    # ------------------------------------------------------------------
    # Data API
    # ------------------------------------------------------------------

    def set_data(self, data: _Series, color: Optional[str] = None) -> None:
        """Replace all series with a single dataset."""
        self._auto_color_idx = 0
        self._series = [(list(data[0]), list(data[1]), color or self._next_color())]
        self.update()

    def add_series(self, data: _Series, color: Optional[str] = None) -> None:
        """Append a data series to the plot."""
        self._series.append((list(data[0]), list(data[1]), color or self._next_color()))
        self.update()

    def clear_series(self) -> None:
        """Remove all data series."""
        self._series.clear()
        self._auto_color_idx = 0
        self.update()

    def _next_color(self) -> str:
        c = _SERIES_COLORS[min(self._auto_color_idx, len(_SERIES_COLORS) - 1)]
        self._auto_color_idx += 1
        return c

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _bounds(self) -> Tuple[float, float, float, float]:
        all_x = [x for xs, ys, _ in self._series for x in xs]
        all_y = [y for xs, ys, _ in self._series for y in ys]
        if not all_x:
            return 0.0, 1.0, 0.0, 1.0
        x_min, x_max = min(all_x), max(all_x)
        y_min, y_max = min(all_y), max(all_y)
        if x_min == x_max:
            x_min -= 1.0
            x_max += 1.0
        if y_min == y_max:
            y_min -= 1.0
            y_max += 1.0
        return x_min, x_max, y_min, y_max

    def _to_px(
        self,
        x: float, y: float,
        bounds: Tuple[float, float, float, float],
        ml: int, mt: int, pw: int, ph: int,
    ) -> Tuple[int, int]:
        x_min, x_max, y_min, y_max = bounds
        if self.log_x and x > 0 and x_min > 0:
            fx = (math.log10(x) - math.log10(x_min)) / (math.log10(x_max) - math.log10(x_min))
        else:
            fx = (x - x_min) / (x_max - x_min)
        if self.log_y and y > 0 and y_min > 0:
            fy = (math.log10(y) - math.log10(y_min)) / (math.log10(y_max) - math.log10(y_min))
        else:
            fy = (y - y_min) / (y_max - y_min)
        return ml + int(fx * pw), mt + int((1.0 - fy) * ph)

    # ------------------------------------------------------------------
    # Painting
    # ------------------------------------------------------------------

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:  # noqa: N802
        p = QtGui.QPainter(self)

        w, h = self.width(), self.height()

        tick_font = QtGui.QFont(self.default_font)
        tick_font.setPointSize(max(10, int(self.default_font.pointSize() * 1.5)))
        fm = QtGui.QFontMetrics(tick_font)

        # Margins computed from font metrics so labels always fit
        ml = fm.horizontalAdvance("-0.000") + 20
        mb = fm.height() + 15
        mr = self._MR
        mt = self._MT
        pw = w - ml - mr
        ph = h - mt - mb

        p.fillRect(0, 0, w, h, QtGui.QColor("#000000"))

        if not self._series or pw <= 0 or ph <= 0:
            p.end()
            return

        bounds = self._bounds()
        x_min, x_max, y_min, y_max = bounds

        y_ticks = (
            _log_ticks(y_min, y_max) if (self.log_y and y_min > 0)
            else _nice_ticks(y_min, y_max, 5)
        )
        x_ticks = (
            _log_ticks(x_min, x_max) if (self.log_x and x_min > 0)
            else _nice_ticks(x_min, x_max, 5)
        )

        axis_col = QtGui.QColor("#ffffff")  # very light grey
        label_col = QtGui.QColor("#fc9")  # beige

        # Grid
        if self.grid:
            grid_col = QtGui.QColor("#aaaaaa")
            p.setPen(QtGui.QPen(grid_col, 4))
            for yt in y_ticks:
                _, py = self._to_px(x_min, yt, bounds, ml, mt, pw, ph)
                if mt <= py <= mt + ph:
                    p.drawLine(ml, py, ml + pw, py)
            for xt in x_ticks:
                px, _ = self._to_px(xt, y_min, bounds, ml, mt, pw, ph)
                if ml <= px <= ml + pw:
                    p.drawLine(px, mt, px, mt + ph)

        # Axes — all four sides
        p.setPen(QtGui.QPen(axis_col, 4))
        p.drawLine(ml, mt, ml, mt + ph)           # left
        p.drawLine(ml, mt + ph, ml + pw, mt + ph) # bottom
        p.drawLine(ml + pw, mt, ml + pw, mt + ph) # right
        p.drawLine(ml, mt, ml + pw, mt)           # top

        # Y ticks and labels
        p.setFont(tick_font)
        for yt in y_ticks:
            _, py = self._to_px(x_min, yt, bounds, ml, mt, pw, ph)
            if mt <= py <= mt + ph:
                p.setPen(QtGui.QPen(axis_col, 4))
                p.drawLine(ml - 5, py, ml, py)
                p.setPen(label_col)
                lbl = _fmt_tick(yt)
                p.drawText(ml - 8 - fm.horizontalAdvance(lbl), py + fm.ascent() // 2, lbl)

        # X ticks and labels
        for xt in x_ticks:
            px, _ = self._to_px(xt, y_min, bounds, ml, mt, pw, ph)
            if ml <= px <= ml + pw:
                p.setPen(QtGui.QPen(axis_col, 4))
                p.drawLine(px, mt + ph, px, mt + ph + 5)
                p.setPen(label_col)
                lbl = _fmt_tick(xt)
                p.drawText(px - fm.horizontalAdvance(lbl) // 2, mt + ph + 5 + fm.height(), lbl)

        # Data lines (clipped to plot area) — drawn as polylines so joins are clean
        p.setClipRect(ml, mt, pw, ph)
        for xs, ys, series_color in self._series:
            if len(xs) < 2:
                continue
            pen = QtGui.QPen(QtGui.QColor(series_color))
            pen.setWidth(self.line_width)
            pen.setJoinStyle(QtCore.Qt.RoundJoin)
            pen.setCapStyle(QtCore.Qt.RoundCap)
            p.setPen(pen)
            pts = [QtCore.QPoint(*self._to_px(x, y, bounds, ml, mt, pw, ph)) for x, y in zip(xs, ys)]
            p.drawPolyline(*pts)

        p.end()
