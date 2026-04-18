# -*- coding: utf-8 -*-
"""C-Style LCARS frame widget.

Thick left sidebar with upper and lower button groups, thin top and bottom bars,
and an open right side forming a 'C' shape around a central display area.
"""
from functools import partial
from typing import Any, Callable, Dict, List, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from .block import Block
from .bracket import Bracket
from .deco import Deco
from .separator import Separator
from .textline import Textline
from ..conditions import Conditions
from ..orientation import Orientation


class CStyleFrame:
    """C-Style LCARS frame: thick left sidebar, thin top/bottom bars, open right.

    The left sidebar holds an upper and lower button group separated by a fill
    block. Corner swish decorations connect the sidebar to the horizontal bars.
    Clicking a button hides the current page and shows the new one.

    Attributes:
        buttons: All button widgets keyed by name.
        pages: Content widget dicts keyed by button name.
        fields: All button names in order (upper then lower).
        active_page: Name of the currently visible page.
        enabled: Whether button interaction is active.
        color: Primary frame color.
        color_active: Color for the active button.
    """

    buttons: Dict[str, Bracket]
    pages: Dict[str, Dict[str, Any]]
    fields: List[str]
    active_page: str
    enabled: bool
    color: str
    color_active: str

    def display_rect(self) -> QtCore.QRect:
        """Return the content area QRect."""
        return self._display_rect

    def set_header_text(self, text: str) -> None:
        """Update the header label text."""
        if self._header_label is not None:
            self._header_label.setText(text)

    def set_footer_text(self, text: str) -> None:
        """Update the footer label text."""
        if self._footer_label is not None:
            self._footer_label.setText(text)

    def frame_click(self, button_name: str = "") -> None:
        """Switch to the named page with visual and audio feedback."""
        if not self.enabled or self.active_page == button_name:
            return
        self.lcars.play_sound()
        self.blend_out(self.active_page)
        self.buttons[self.active_page].tockle()
        self.active_page = button_name
        self.buttons[self.active_page].tockle(self.color_active)
        self.blend_in(self.active_page)

    def blend_out(self, page: str) -> None:
        """Hide all widgets registered to a page."""
        for widget in self.pages[page].values():
            widget.hide()

    def blend_in(self, page: str) -> None:
        """Show all widgets registered to a page."""
        for widget in self.pages[page].values():
            widget.show()

    def paint_back(self, color: str) -> None:
        """Repaint all frame chrome and buttons with a new color."""
        for name in self.fields:
            self.buttons[name].paint_back(color)
        for widget in self._chrome:
            widget.paint_back(color)

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    def __init__(
        self,
        lcars: QtWidgets.QWidget,
        rect: QtCore.QRect,
        upper_buttons: List[str],
        lower_buttons: List[str],
        padding: int = 5,
        thin_thickness: int = 20,
        thick_thickness: int = 195,
        button_spacing: int = 4,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        color: str = Conditions.use,
        color_active: str = Conditions.active,
        button_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialise a C-Style frame.

        Args:
            lcars: Parent LCARS window.
            rect: Bounding rectangle for the entire frame.
            upper_buttons: Button names for the top button group.
            lower_buttons: Button names for the bottom button group.
            padding: Gap between bounding rect and frame chrome (px).
            thin_thickness: Height of the top and bottom bars (px).
            thick_thickness: Total width of the left sidebar (px).
            button_spacing: Vertical gap between buttons and chrome (px).
            header_text: Optional label on the top bar.
            footer_text: Optional label on the bottom bar.
            color: Primary frame color.
            color_active: Color applied to the active button.
            button_callback: Override for the default page-switch handler.
        """
        self.lcars = lcars
        self.color = color
        self.color_active = color_active
        self.enabled = True
        self._header_label: Optional[Textline] = None
        self._footer_label: Optional[Textline] = None

        t = thin_thickness
        T = thick_thickness
        bh = 2 * t          # button / separator height
        bw = int(T * 2 / 3)  # button width (separator occupies bw + bh/2 = T)
        bs = button_spacing

        ix = rect.x() + padding
        iy = rect.y() + padding
        iw = rect.width() - 2 * padding
        ih = rect.height() - 2 * padding

        bar_x = ix + T + bs
        bar_w = iw - T - bs
        bar_right = ix + iw

        # ── Corner swish decorations ──────────────────────────────────────
        top_sep = Separator(
            lcars, QtCore.QRect(ix, iy, T, bh), color, bw,
            orientation=Orientation.top,
        )
        bot_sep = Separator(
            lcars, QtCore.QRect(ix, iy + ih - bh, T, bh), color, bw,
            orientation=Orientation.bottom,
        )

        # ── Thin horizontal bars ──────────────────────────────────────────
        top_bar = Block(lcars, QtCore.QRect(bar_x, iy, bar_w, t), color)
        bot_bar = Block(lcars, QtCore.QRect(bar_x, iy + ih - t, bar_w, t), color)

        # ── Right-end caps (always present) ───────────────────────────────
        top_cap = self._make_cap(lcars, bar_right - t, iy, t, color)
        bot_cap = self._make_cap(lcars, bar_right - t, iy + ih - t, t, color)

        self._chrome = [top_sep, bot_sep, top_bar, bot_bar, top_cap, bot_cap]

        # ── Optional bar text labels ──────────────────────────────────────
        if header_text is not None:
            self._header_label = self._add_text(
                lcars, bar_right - t, iy, t, color, header_text,
            )
        if footer_text is not None:
            self._footer_label = self._add_text(
                lcars, bar_right - t, iy + ih - t, t, color, footer_text,
            )

        # ── Display area ──────────────────────────────────────────────────
        self._display_rect = QtCore.QRect(
            bar_x,
            iy + bh + bs,
            bar_w - t,
            ih - 2 * bh - bs,
        )

        # ── Buttons ───────────────────────────────────────────────────────
        self.buttons = {}
        self.pages = {}
        self.fields = list(upper_buttons) + list(lower_buttons)
        self.button_callback = button_callback or self.frame_click

        # Upper group – stacked downward from the top separator
        pos_y = iy + bh + bs
        for name in upper_buttons:
            self.buttons[name] = Bracket(
                lcars, QtCore.QRect(ix, pos_y, bw, bh), name + " ", color,
            )
            self.buttons[name].clicked.connect(
                partial(self.button_callback, button_name=name),
            )
            self._unbold(self.buttons[name])
            self.pages[name] = {}
            pos_y += bh + bs
        upper_end_y = pos_y

        # Lower group – packed against the bottom separator, stacked downward
        n_lower = len(lower_buttons)
        lower_gap = n_lower * (bh + bs) if n_lower > 0 else bs
        lower_start_y = iy + ih - bh - lower_gap
        for i, name in enumerate(lower_buttons):
            btn_y = lower_start_y + i * (bh + bs)
            self.buttons[name] = Bracket(
                lcars, QtCore.QRect(ix, btn_y, bw, bh), name + " ", color,
            )
            self.buttons[name].clicked.connect(
                partial(self.button_callback, button_name=name),
            )
            self._unbold(self.buttons[name])
            self.pages[name] = {}

        # Fill block bridges the gap between the two button groups
        fill_h = lower_start_y - upper_end_y
        if fill_h > 0:
            fill = Block(lcars, QtCore.QRect(ix, upper_end_y, bw, fill_h), color)
            self._chrome.append(fill)

        # ── Initial state ─────────────────────────────────────────────────
        if self.fields:
            self.active_page = self.fields[0]
            self.buttons[self.active_page].tockle(color_active)
        else:
            self.active_page = ""

    # ── Private helpers ───────────────────────────────────────────────────

    @staticmethod
    def _make_cap(
        lcars: QtWidgets.QWidget, x: int, y: int, t: int, color: str,
    ) -> Deco:
        """Render a rounded right-end cap for a horizontal bar."""
        r = t / 2
        svg = (
            f'<svg height="{t}" width="{t}">'
            f'<rect x="0" y="0" width="{r}" height="{t}" fill="{{c}}" />'
            f'<circle cx="{r}" cy="{r}" r="{r}" fill="{{c}}" />'
            f'</svg>'
        )
        return Deco(lcars, QtCore.QRect(x, y, t, t), color, svg=svg)

    @staticmethod
    def _add_text(
        lcars: QtWidgets.QWidget,
        cap_x: int,
        y: int,
        t: int,
        color: str,
        text: str,
    ) -> Textline:
        """Render a text label cut into a horizontal bar, left of the end cap."""
        font_size = 24
        gap = 12
        text_w = (
            QtGui.QFontMetrics(QtGui.QFont("LCARS", font_size)).horizontalAdvance(text)
            + 16
        )
        text_x = cap_x - gap - text_w
        text_rect = QtCore.QRect(text_x, y, text_w, t)
        Block(lcars, text_rect, "#000000")
        label = Textline(lcars, text_rect, color, font_size)
        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        CStyleFrame._unbold(label)
        return label

    @staticmethod
    def _unbold(widget: QtWidgets.QWidget) -> None:
        f = widget.font()
        f.setBold(False)
        widget.setFont(f)
