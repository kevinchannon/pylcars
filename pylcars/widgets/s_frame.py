# -*- coding: utf-8 -*-
"""S-Frame: split-sidebar LCARS frame widget."""
from typing import Any, Callable, Dict, List, Optional

from PyQt5 import QtCore, QtWidgets

from .bar_label import BarLabel
from .block import Block
from .bracket import Bracket
from .deco import Deco
from ..conditions import Conditions
from .. import config
from .frame import Frame, bar_thickness, points_for_height
from .frame_support import (
    MIN_BUTTON_HEIGHT,
    SidebarButtons,
    check_button_names,
    resolve_play_sound,
)
from ..button_info import ButtonSpec, _btn_name


class SFrame(SidebarButtons):
    """LCARS S-Style (split-sidebar) frame.

    One sidebar occupies the upper half, the other the lower half, connected
    by a thin horizontal mid-bar. Optional top and bottom bars can cap the frame.

    The two halves are independently addressable: upper buttons switch pages in
    ``upper_pages`` and lower buttons switch pages in ``lower_pages``.  Both
    halves key into one ``buttons`` dict, so button names must be unique across
    the frame; give two buttons the same label with ``ButtonInfo.text`` rather
    than the same name.

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

    def set_header_text(self, text: str) -> None:
        """Set the top bar text, resizing the gap in the bar to match.

        Does nothing when the frame was created without ``header_text``.

        Args:
            text: New header text.
        """
        if self._header_label is not None:
            self._header_label.setText(text)

    def set_footer_text(self, text: str) -> None:
        """Set the bottom bar text, resizing the gap in the bar to match.

        Does nothing when the frame was created without ``footer_text``.

        Args:
            text: New footer text.
        """
        if self._footer_label is not None:
            self._footer_label.setText(text)

    def set_title_text(self, text: str) -> None:
        """Set the mid-bar title, resizing the gap in the bar to match.

        Does nothing when the frame was created without ``title``.

        Args:
            text: New mid-bar title.
        """
        if self._title_label is not None:
            self._title_label.setText(text)

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
        """Switch the upper half to the named page, with visual and audio feedback."""
        if not self.enabled or self.upper_active_page == button_name:
            return
        self._play_sound()
        self.upper_blend_out(self.upper_active_page)
        self.buttons[self.upper_active_page].tockle()
        self.upper_active_page = button_name
        self.buttons[self.upper_active_page].tockle(self._active_color(self.upper_active_page))
        self.upper_blend_in(self.upper_active_page)

    def lower_frame_click(self, button_name: str = "") -> None:
        """Switch the lower half to the named page, with visual and audio feedback."""
        if not self.enabled or self.lower_active_page == button_name:
            return
        self._play_sound()
        self.lower_blend_out(self.lower_active_page)
        self.buttons[self.lower_active_page].tockle()
        self.lower_active_page = button_name
        self.buttons[self.lower_active_page].tockle(self._active_color(self.lower_active_page))
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
        parent: QtWidgets.QWidget,
        rect: QtCore.QRect,
        mirror: bool = False,
        upper_buttons: Optional[List[ButtonSpec]] = None,
        lower_buttons: Optional[List[ButtonSpec]] = None,
        split: float = 0.5,
        has_top: bool = False,
        has_bottom: bool = False,
        title: Optional[str] = None,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        padding: int = 4,
        thin_thickness: int = 20,
        thick_thickness: int = 200,
        button_spacing: int = 4,
        color: str = Conditions.use,
        color_active: str = Conditions.active,
        upper_button_callback: Optional[Callable[[str], None]] = None,
        lower_button_callback: Optional[Callable[[str], None]] = None,
        button_texts: Optional[Dict[str, str]] = None,
        button_font_size: Optional[int] = None,
        play_sound: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialise an SFrame.

        Args:
            parent: Widget the frame is built on.  Any QWidget will do — an
                Lcars window, or a plain container so the frame can be shown,
                hidden and moved as one object.
            rect: Bounding rectangle for the entire frame.
            mirror: False = right sidebar top / left sidebar bottom.
                    True  = left sidebar top / right sidebar bottom.
            upper_buttons: Buttons for the upper (top-half) sidebar (str or ButtonInfo).
            lower_buttons: Buttons for the lower (bottom-half) sidebar (str or ButtonInfo).
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
            button_texts: Display labels keyed by button name, for buttons whose
                label should differ from their key.  ``ButtonInfo.text`` wins
                where both are given.
            button_font_size: Point size for sidebar button text. When ``None``
                (default) the Bracket default font size is used.
            play_sound: Called on each page switch.  When ``None`` (default) the
                parent's ``play_sound`` is used if it has one, and the frame is
                silent otherwise.

        Raises:
            ValueError: If a button name is used more than once.  Both halves
                key into the same ``buttons`` dict, so names must be unique
                across the frame; use ``ButtonInfo.text`` to give two buttons
                in different halves the same label.
        """
        upper_buttons = upper_buttons or []
        lower_buttons = lower_buttons or []

        check_button_names(upper_buttons, lower_buttons)

        self.parent = parent
        self.color = color
        self.color_active = color_active
        self._play_sound = resolve_play_sound(parent, play_sound)
        self.enabled = True
        self._chrome: list = []
        self._header_label: Optional[BarLabel] = None
        self._footer_label: Optional[BarLabel] = None
        self._title_label: Optional[BarLabel] = None

        t = bar_thickness(thin_thickness)
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
            self._chrome.append(Deco(parent, QtCore.QRect(upper_sx, iy, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(parent, QtCore.QRect(upper_bx, iy, bw, bh), color))

        # Bottom of upper sidebar → mid junction (bar at SVG y=t, place at mid_y - t)
        svg = Frame._corner_svg(T, bh, t, bar, top=False, left=(upper_side == 'left'))
        self._chrome.append(Deco(parent, QtCore.QRect(upper_sx, mid_y - t, T, bh), color, svg=svg))

        # ── Lower sidebar ─────────────────────────────────────────────────
        # Top of lower sidebar → mid junction (bar at SVG y=0, place at mid_y)
        svg = Frame._corner_svg(T, bh, t, bar, top=True, left=(lower_side == 'left'))
        self._chrome.append(Deco(parent, QtCore.QRect(lower_sx, mid_y, T, bh), color, svg=svg))

        if has_bottom:
            svg = Frame._corner_svg(T, bh, t, bar, top=False, left=(lower_side == 'left'))
            self._chrome.append(Deco(parent, QtCore.QRect(lower_sx, iy + ih - bh, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(parent, QtCore.QRect(lower_bx, iy + ih - bh, bw, bh), color))

        # ── Mid-bar ───────────────────────────────────────────────────────
        mb_x = ix + T + bs
        mb_w = iw - 2 * T - 2 * bs
        self._chrome.append(Block(parent, QtCore.QRect(mb_x, mid_y, mb_w, t), color))
        if title:
            font_size = points_for_height(config.DEFAULT_FONT_NAME, t)
            self._title_label = BarLabel(
                parent, mb_x + mb_w, mid_y, t, color, font_size,
                gap=0, padding_chars=2, letter_spacing=1,
            )
            self._title_label.setText(title)
            self._chrome.append(self._title_label)

        # ── Optional top bar ──────────────────────────────────────────────
        if has_top:
            if upper_side == 'right':
                tb_x, tb_w, cap_x, cap_side = ix, iw - T - bs, ix, 'left'
            else:
                tb_x, tb_w = ix + T + bs, iw - T - bs
                cap_x, cap_side = tb_x + tb_w - t, 'right'
            self._chrome.append(Block(parent, QtCore.QRect(tb_x, iy, tb_w, t), color))
            self._chrome.append(Frame._make_cap(parent, cap_x, iy, t, color, side=cap_side))
            if header_text:
                anchor = tb_x if cap_side == 'left' else tb_x + tb_w
                self._header_label = Frame._add_text(
                    parent, anchor, iy, t, color, header_text, align_left=(cap_side == 'left'),
                )
                self._chrome.append(self._header_label)

        # ── Optional bottom bar ───────────────────────────────────────────
        if has_bottom:
            bot_bar_y = iy + ih - t
            if lower_side == 'left':
                bb_x, bb_w = ix + T + bs, iw - T - bs
                cap_x, cap_side = bb_x + bb_w - t, 'right'
            else:
                bb_x, bb_w, cap_x, cap_side = ix, iw - T - bs, ix, 'left'
            self._chrome.append(Block(parent, QtCore.QRect(bb_x, bot_bar_y, bb_w, t), color))
            self._chrome.append(Frame._make_cap(parent, cap_x, bot_bar_y, t, color, side=cap_side))
            if footer_text:
                anchor = bb_x + bb_w if cap_side == 'right' else bb_x
                self._footer_label = Frame._add_text(
                    parent, anchor, bot_bar_y, t, color, footer_text,
                    align_left=(cap_side == 'left'),
                )
                self._chrome.append(self._footer_label)

        # ── Buttons and pages ─────────────────────────────────────────────
        self._init_buttons(
            button_texts=button_texts,
            button_font_size=button_font_size,
            min_button_height=max(MIN_BUTTON_HEIGHT, bh),
        )
        self.upper_pages: Dict[str, Dict[str, Any]] = {}
        self.lower_pages: Dict[str, Dict[str, Any]] = {}
        self.upper_fields = [_btn_name(s) for s in upper_buttons]
        self.lower_fields = [_btn_name(s) for s in lower_buttons]
        self.fields = self.upper_fields + self.lower_fields

        upper_cb = upper_button_callback or self.upper_frame_click
        lower_cb = lower_button_callback or self.lower_frame_click

        # One column per half: a single group running top-down, with the
        # remainder of the half filled by a Block.
        self._add_button_column(
            parent, self._chrome,
            x=upper_bx, w=bw,
            top_y=iy + bh + bs, bot_y=mid_y - t, spacing=bs,
            callback=upper_cb, pages=self.upper_pages,
            top_group=upper_buttons, side=upper_side,
        )
        self._add_button_column(
            parent, self._chrome,
            x=lower_bx, w=bw,
            top_y=mid_y + bh + bs, bot_y=iy + ih - bh, spacing=bs,
            callback=lower_cb, pages=self.lower_pages,
            top_group=lower_buttons, side=lower_side,
        )

        self.upper_active_page = self.upper_fields[0] if self.upper_fields else ""
        self.lower_active_page = self.lower_fields[0] if self.lower_fields else ""

        if self.upper_active_page:
            self.buttons[self.upper_active_page].tockle(self._active_color(self.upper_active_page))
        if self.lower_active_page:
            self.buttons[self.lower_active_page].tockle(self._active_color(self.lower_active_page))

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
