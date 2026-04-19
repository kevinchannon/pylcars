# -*- coding: utf-8 -*-
"""S-Frame: split-sidebar LCARS frame widget."""
from functools import partial
from typing import Any, Callable, Dict, List, Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from .block import Block
from .bracket import Bracket
from .deco import Deco
from .textline import Textline
from ..conditions import Conditions
from .frame import Frame


class SFrame:
    """LCARS S-Style (split-sidebar) frame.

    One sidebar occupies the upper half, the other the lower half, connected
    by a thin horizontal mid-bar. Optional top and bottom bars can cap the frame.

    The two halves are independently addressable: upper buttons switch pages in
    ``upper_pages`` and lower buttons switch pages in ``lower_pages``.

    ``mirror=False``: right sidebar on top, left on bottom.
    ``mirror=True``:  left sidebar on top, right on bottom.
    """

    buttons: Dict[str, Bracket]
    upper_pages: Dict[str, Dict[str, Any]]
    lower_pages: Dict[str, Dict[str, Any]]
    upper_fields: List[str]
    lower_fields: List[str]
    fields: List[str]
    upper_active_page: str
    lower_active_page: str
    enabled: bool
    color: str
    color_active: str

    # ── Public API ────────────────────────────────────────────────────────

    def upper_display_rect(self) -> QtCore.QRect:
        """Content area in the upper half (opposite the upper sidebar)."""
        return self._upper_display_rect

    def lower_display_rect(self) -> QtCore.QRect:
        """Content area in the lower half (opposite the lower sidebar)."""
        return self._lower_display_rect

    def display_rect(self) -> QtCore.QRect:
        """Central column between both sidebar positions (safe area at any height)."""
        return self._display_rect

    def upper_blend_in(self, page: str) -> None:
        for widget in self.upper_pages[page].values():
            widget.show()

    def upper_blend_out(self, page: str) -> None:
        for widget in self.upper_pages[page].values():
            widget.hide()

    def lower_blend_in(self, page: str) -> None:
        for widget in self.lower_pages[page].values():
            widget.show()

    def lower_blend_out(self, page: str) -> None:
        for widget in self.lower_pages[page].values():
            widget.hide()

    def upper_frame_click(self, button_name: str = "") -> None:
        if not self.enabled or self.upper_active_page == button_name:
            return
        self.lcars.play_sound()
        self.upper_blend_out(self.upper_active_page)
        self.buttons[self.upper_active_page].tockle()
        self.upper_active_page = button_name
        self.buttons[self.upper_active_page].tockle(self.color_active)
        self.upper_blend_in(self.upper_active_page)

    def lower_frame_click(self, button_name: str = "") -> None:
        if not self.enabled or self.lower_active_page == button_name:
            return
        self.lcars.play_sound()
        self.lower_blend_out(self.lower_active_page)
        self.buttons[self.lower_active_page].tockle()
        self.lower_active_page = button_name
        self.buttons[self.lower_active_page].tockle(self.color_active)
        self.lower_blend_in(self.lower_active_page)

    def paint_back(self, color: str) -> None:
        for name in self.fields:
            self.buttons[name].paint_back(color)
        for widget in self._chrome:
            widget.paint_back(color)

    def setEnabled(self, enabled: bool) -> None:
        self.enabled = enabled

    # ── Initialisation ────────────────────────────────────────────────────

    def __init__(
        self,
        lcars: QtWidgets.QWidget,
        rect: QtCore.QRect,
        mirror: bool = False,
        upper_buttons: Optional[List[str]] = None,
        lower_buttons: Optional[List[str]] = None,
        split: float = 0.5,
        has_top: bool = False,
        has_bottom: bool = False,
        title: Optional[str] = None,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        padding: int = 5,
        thin_thickness: int = 20,
        thick_thickness: int = 195,
        button_spacing: int = 4,
        color: str = Conditions.use,
        color_active: str = Conditions.active,
        upper_button_callback: Optional[Callable[[str], None]] = None,
        lower_button_callback: Optional[Callable[[str], None]] = None,
    ) -> None:
        """Initialise an SFrame.

        Args:
            lcars: Parent LCARS window.
            rect: Bounding rectangle for the entire frame.
            mirror: False = right sidebar top / left sidebar bottom.
                    True  = left sidebar top / right sidebar bottom.
            upper_buttons: Button names for the upper (top-half) sidebar.
            lower_buttons: Button names for the lower (bottom-half) sidebar.
            split: Fractional vertical position of the mid-bar (0.0–1.0).
            has_top: Draw a thin bar across the top of the frame.
            has_bottom: Draw a thin bar across the bottom of the frame.
            title: Label on the central mid-bar (right-aligned).
            header_text: Label on the top bar (only meaningful when has_top=True).
            footer_text: Label on the bottom bar (only meaningful when has_bottom=True).
            padding: Gap between bounding rect and frame chrome (px).
            thin_thickness: Height of thin bars (px).
            thick_thickness: Total sidebar width (px).
            button_spacing: Gap between consecutive chrome elements (px).
            color: Primary frame color.
            color_active: Color for the active button.
            upper_button_callback: Override for the upper half page-switch handler.
            lower_button_callback: Override for the lower half page-switch handler.
        """
        upper_buttons = upper_buttons or []
        lower_buttons = lower_buttons or []

        self.lcars = lcars
        self.color = color
        self.color_active = color_active
        self.enabled = True
        self._chrome: list = []

        t = thin_thickness
        T = thick_thickness
        bh = 2 * t
        bw = int(T * 2 / 3)
        bar = bw + t
        bs = button_spacing

        ix = rect.x() + padding
        iy = rect.y() + padding
        iw = rect.width() - 2 * padding
        ih = rect.height() - 2 * padding

        mid_y = iy + int(ih * max(0.0, min(1.0, split)))

        upper_side = 'right' if not mirror else 'left'
        lower_side = 'left' if not mirror else 'right'

        upper_sx = ix + iw - T if upper_side == 'right' else ix
        upper_bx = ix + iw - bw if upper_side == 'right' else ix
        lower_sx = ix if lower_side == 'left' else ix + iw - T
        lower_bx = ix if lower_side == 'left' else ix + iw - bw

        # ── Upper sidebar ─────────────────────────────────────────────────
        if has_top:
            svg = Frame._corner_svg(T, bh, t, bar, top=True, left=(upper_side == 'left'))
            self._chrome.append(Deco(lcars, QtCore.QRect(upper_sx, iy, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(lcars, QtCore.QRect(upper_bx, iy, bw, bh), color))

        # Bottom of upper sidebar → mid junction (bar at SVG y=t, place at mid_y - t)
        svg = Frame._corner_svg(T, bh, t, bar, top=False, left=(upper_side == 'left'))
        self._chrome.append(Deco(lcars, QtCore.QRect(upper_sx, mid_y - t, T, bh), color, svg=svg))

        # ── Lower sidebar ─────────────────────────────────────────────────
        # Top of lower sidebar → mid junction (bar at SVG y=0, place at mid_y)
        svg = Frame._corner_svg(T, bh, t, bar, top=True, left=(lower_side == 'left'))
        self._chrome.append(Deco(lcars, QtCore.QRect(lower_sx, mid_y, T, bh), color, svg=svg))

        if has_bottom:
            svg = Frame._corner_svg(T, bh, t, bar, top=False, left=(lower_side == 'left'))
            self._chrome.append(Deco(lcars, QtCore.QRect(lower_sx, iy + ih - bh, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(lcars, QtCore.QRect(lower_bx, iy + ih - bh, bw, bh), color))

        # ── Mid-bar ───────────────────────────────────────────────────────
        mb_x = ix + T + bs
        mb_w = iw - 2 * T - 2 * bs
        self._chrome.append(Block(lcars, QtCore.QRect(mb_x, mid_y, mb_w, t), color))
        if title:
            font_size = max(8, int(t * 1.3) - 2)
            text_w = QtGui.QFontMetrics(QtGui.QFont("LCARS", font_size)).horizontalAdvance(title) + 16
            text_rect = QtCore.QRect(mb_x + mb_w - text_w, mid_y, text_w, t)
            Block(lcars, text_rect, "#000000")
            lbl = Textline(lcars, text_rect, color, font_size)
            lbl.setText(title)
            lbl.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
            Frame._unbold(lbl)
            self._chrome.append(lbl)

        # ── Optional top bar ──────────────────────────────────────────────
        if has_top:
            if upper_side == 'right':
                tb_x, tb_w, cap_x, cap_side = ix, iw - T - bs, ix, 'left'
            else:
                tb_x, tb_w = ix + T + bs, iw - T - bs
                cap_x, cap_side = tb_x + tb_w - t, 'right'
            self._chrome.append(Block(lcars, QtCore.QRect(tb_x, iy, tb_w, t), color))
            self._chrome.append(Frame._make_cap(lcars, cap_x, iy, t, color, side=cap_side))
            if header_text:
                anchor = tb_x if cap_side == 'left' else tb_x + tb_w
                self._chrome.append(Frame._add_text(
                    lcars, anchor, iy, t, color, header_text, align_left=(cap_side == 'left'),
                ))

        # ── Optional bottom bar ───────────────────────────────────────────
        if has_bottom:
            bot_bar_y = iy + ih - t
            if lower_side == 'left':
                bb_x, bb_w = ix + T + bs, iw - T - bs
                cap_x, cap_side = bb_x + bb_w - t, 'right'
            else:
                bb_x, bb_w, cap_x, cap_side = ix, iw - T - bs, ix, 'left'
            self._chrome.append(Block(lcars, QtCore.QRect(bb_x, bot_bar_y, bb_w, t), color))
            self._chrome.append(Frame._make_cap(lcars, cap_x, bot_bar_y, t, color, side=cap_side))
            if footer_text:
                anchor = bb_x + bb_w if cap_side == 'right' else bb_x
                self._chrome.append(Frame._add_text(
                    lcars, anchor, bot_bar_y, t, color, footer_text,
                    align_left=(cap_side == 'left'),
                ))

        # ── Buttons and pages ─────────────────────────────────────────────
        self.buttons = {}
        self.upper_pages: Dict[str, Dict[str, Any]] = {}
        self.lower_pages: Dict[str, Dict[str, Any]] = {}
        self.upper_fields = list(upper_buttons)
        self.lower_fields = list(lower_buttons)
        self.fields = self.upper_fields + self.lower_fields

        upper_cb = upper_button_callback or self.upper_frame_click
        lower_cb = lower_button_callback or self.lower_frame_click

        self._place_btns(
            lcars, upper_bx, iy + bh + bs, mid_y - t,
            bh, bw, bs, upper_buttons, self.upper_pages, upper_cb,
        )
        self._place_btns(
            lcars, lower_bx, mid_y + bh + bs, iy + ih - bh,
            bh, bw, bs, lower_buttons, self.lower_pages, lower_cb,
        )

        self.upper_active_page = self.upper_fields[0] if self.upper_fields else ""
        self.lower_active_page = self.lower_fields[0] if self.lower_fields else ""

        if self.upper_active_page:
            self.buttons[self.upper_active_page].tockle(color_active)
        if self.lower_active_page:
            self.buttons[self.lower_active_page].tockle(color_active)

        # ── Display rects ─────────────────────────────────────────────────
        # Vertical bounds: content spans between corner pieces (always bh=2t tall).
        # Horizontal bounds: on the sidebar side, exclude T+bs; on the free side,
        # inset by t to align with the leftmost/rightmost point of the bar end cap
        # (present in the swish geometry regardless of whether the bar is visible).
        udr_y = iy if not has_top else iy + bh + bs
        udr_bot = mid_y - t           # always: top of the mid-junction corner piece
        udr_x = ix + t if upper_side == 'right' else ix + T + bs
        udr_w = iw - T - bs - t
        udr_h = udr_bot - udr_y
        self._upper_display_rect = QtCore.QRect(udr_x, udr_y, udr_w, udr_h)

        ldr_y = mid_y + bh + bs       # always: below the mid-junction corner piece
        ldr_bot = iy + ih if not has_bottom else iy + ih - bh
        ldr_x = ix + T + bs if lower_side == 'left' else ix + t
        ldr_w = iw - T - bs - t
        ldr_h = ldr_bot - ldr_y
        self._lower_display_rect = QtCore.QRect(ldr_x, ldr_y, ldr_w, ldr_h)

        self._display_rect = QtCore.QRect(
            ix + T + bs, udr_y, iw - 2 * T - 2 * bs, ldr_bot - udr_y,
        )


    # ── Private helpers ───────────────────────────────────────────────────

    def _place_btns(
        self,
        lcars: QtWidgets.QWidget,
        btn_x: int,
        top_y: int,
        bot_y: int,
        bh: int,
        bw: int,
        bs: int,
        names: List[str],
        pages: Dict[str, Dict[str, Any]],
        callback: Callable,
    ) -> None:
        """Place a button group from top_y downward; fill remaining space."""
        pos_y = top_y
        for name in names:
            self.buttons[name] = Bracket(
                lcars, QtCore.QRect(btn_x, pos_y, bw, bh), name + " ", self.color,
            )
            self.buttons[name].clicked.connect(partial(callback, button_name=name))
            Frame._unbold(self.buttons[name])
            pages[name] = {}
            pos_y += bh + bs
        fill_h = bot_y - pos_y
        if fill_h > 0:
            self._chrome.append(Block(lcars, QtCore.QRect(btn_x, pos_y, bw, fill_h), self.color))
