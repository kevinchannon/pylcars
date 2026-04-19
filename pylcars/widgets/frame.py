# -*- coding: utf-8 -*-
"""Generic LCARS frame widget driven by a set of visible borders."""
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Set

from PyQt5 import QtCore, QtGui, QtWidgets

from .block import Block
from .bracket import Bracket
from .deco import Deco
from .separator import Separator
from .textline import Textline
from ..conditions import Conditions
from ..frame_border import FrameBorder
from ..orientation import Orientation


class Frame:
    """LCARS frame whose visible borders are selected via a set of FrameBorder values.

    Each visible sidebar (LEFT / RIGHT) may carry an upper and lower button
    group.  Clicking any button hides the previous page and shows the new one,
    matching the behaviour of Menue.

    Attributes:
        buttons: All button widgets keyed by name.
        pages: Content widget dicts keyed by button name.
        fields: All button names in order (left-upper, left-lower,
            right-upper, right-lower).
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

    # ── Public API ────────────────────────────────────────────────────────

    def display_rect(self) -> QtCore.QRect:
        """Return the content area QRect."""
        return self._display_rect

    def set_header_text(self, text: str) -> None:
        if self._header_label is not None:
            self._header_label.setText(text)

    def set_footer_text(self, text: str) -> None:
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
        for widget in self.pages[page].values():
            widget.hide()

    def blend_in(self, page: str) -> None:
        for widget in self.pages[page].values():
            widget.show()

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
        borders: Set[FrameBorder],
        left_upper_buttons: Optional[List[str]] = None,
        left_lower_buttons: Optional[List[str]] = None,
        right_upper_buttons: Optional[List[str]] = None,
        right_lower_buttons: Optional[List[str]] = None,
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
        """Initialise a Frame.

        Args:
            lcars: Parent LCARS window.
            rect: Bounding rectangle for the entire frame.
            borders: Set of FrameBorder values selecting which sides are drawn.
            left_upper_buttons: Button names for the top of the left sidebar.
            left_lower_buttons: Button names for the bottom of the left sidebar.
            right_upper_buttons: Button names for the top of the right sidebar.
            right_lower_buttons: Button names for the bottom of the right sidebar.
            padding: Gap between bounding rect and frame chrome (px).
            thin_thickness: Height of the horizontal bars (px).
            thick_thickness: Total width of each sidebar (px).
            button_spacing: Gap between consecutive chrome elements (px).
            header_text: Optional label on the top bar.
            footer_text: Optional label on the bottom bar.
            color: Primary frame color.
            color_active: Color for the active button.
            button_callback: Override for the default page-switch handler.
        """
        left_upper_buttons = left_upper_buttons or []
        left_lower_buttons = left_lower_buttons or []
        right_upper_buttons = right_upper_buttons or []
        right_lower_buttons = right_lower_buttons or []

        self.lcars = lcars
        self.color = color
        self.color_active = color_active
        self.enabled = True
        self._header_label: Optional[Textline] = None
        self._footer_label: Optional[Textline] = None
        self._chrome: list = []

        has_top = FrameBorder.TOP in borders
        has_bot = FrameBorder.BOTTOM in borders
        has_left = FrameBorder.LEFT in borders
        has_right = FrameBorder.RIGHT in borders

        t = thin_thickness
        T = thick_thickness
        bh = 2 * t
        bw = int(T * 2 / 3)
        bar = bw + t          # Separator internal bar_width value
        bs = button_spacing

        ix = rect.x() + padding
        iy = rect.y() + padding
        iw = rect.width() - 2 * padding
        ih = rect.height() - 2 * padding

        # ── Left sidebar ──────────────────────────────────────────────────
        if has_left:
            self._build_sidebar(
                lcars, ix, iy, iw, ih,
                T, bh, bw, bar, t, bs, color,
                side='left', has_top=has_top, has_bot=has_bot,
            )

        # ── Right sidebar ─────────────────────────────────────────────────
        if has_right:
            self._build_sidebar(
                lcars, ix, iy, iw, ih,
                T, bh, bw, bar, t, bs, color,
                side='right', has_top=has_top, has_bot=has_bot,
            )

        # ── Horizontal bars ───────────────────────────────────────────────
        bar_left = ix + (T + bs if has_left else 0)
        bar_right_x = ix + iw - (T + bs if has_right else 0)
        bar_w = bar_right_x - bar_left

        align_left = has_right and not has_left
        text_x_anchor = (
            bar_left + (t if not has_left else 0)
            if align_left
            else bar_right_x - (t if not has_right else 0)
        )

        if has_top:
            top_bar = Block(lcars, QtCore.QRect(bar_left, iy, bar_w, t), color)
            self._chrome.append(top_bar)
            if not has_left:
                self._chrome.append(self._make_cap(lcars, bar_left, iy, t, color, side='left'))
            if not has_right:
                self._chrome.append(self._make_cap(lcars, bar_right_x - t, iy, t, color, side='right'))
            if header_text is not None:
                self._header_label = self._add_text(
                    lcars, text_x_anchor, iy, t, color, header_text, align_left=align_left,
                )

        if has_bot:
            bot_y = iy + ih - t
            bot_bar = Block(lcars, QtCore.QRect(bar_left, bot_y, bar_w, t), color)
            self._chrome.append(bot_bar)
            if not has_left:
                self._chrome.append(self._make_cap(lcars, bar_left, bot_y, t, color, side='left'))
            if not has_right:
                self._chrome.append(self._make_cap(lcars, bar_right_x - t, bot_y, t, color, side='right'))
            if footer_text is not None:
                self._footer_label = self._add_text(
                    lcars, text_x_anchor, bot_y, t, color, footer_text, align_left=align_left,
                )

        # ── Display rect ──────────────────────────────────────────────────
        if has_left or has_right:
            display_y = iy + bh + bs
            display_bot = iy + ih - bh
        elif has_top:
            display_y = iy + t + bs
            display_bot = iy + ih - (t if has_bot else 0)
        else:
            display_y = iy
            display_bot = iy + ih - (t if has_bot else 0)

        has_any_bar = has_top or has_bot
        display_x = ix + (T + bs if has_left else (t if has_any_bar else 0))
        display_right = ix + iw - (T + bs if has_right else (t if has_any_bar else 0))

        self._display_rect = QtCore.QRect(
            display_x,
            display_y,
            display_right - display_x,
            display_bot - display_y,
        )

        # ── Buttons ───────────────────────────────────────────────────────
        self.buttons = {}
        self.pages = {}
        self.fields = (
            list(left_upper_buttons) + list(left_lower_buttons)
            + list(right_upper_buttons) + list(right_lower_buttons)
        )
        self.button_callback = button_callback or self.frame_click

        self._place_buttons(
            lcars, ix, iy, iw, ih, bh, bw, bs,
            left_upper_buttons, left_lower_buttons, side='left', has_sidebar=has_left,
        )
        self._place_buttons(
            lcars, ix, iy, iw, ih, bh, bw, bs,
            right_upper_buttons, right_lower_buttons, side='right', has_sidebar=has_right,
        )

        if self.fields:
            self.active_page = self.fields[0]
            self.buttons[self.active_page].tockle(color_active)
        else:
            self.active_page = ""

    # ── Private geometry helpers ──────────────────────────────────────────

    def _build_sidebar(
        self,
        lcars: QtWidgets.QWidget,
        ix: int, iy: int, iw: int, ih: int,
        T: int, bh: int, bw: int, bar: int, t: int, bs: int,
        color: str,
        side: str,
        has_top: bool,
        has_bot: bool,
    ) -> None:
        """Build one sidebar's corner pieces and fill block."""
        sx = ix if side == 'left' else ix + iw - T
        btn_x = ix if side == 'left' else ix + iw - bw

        # Top corner: swish into the horizontal bar, or plain rect if no top bar
        if has_top:
            svg = self._corner_svg(T, bh, t, bar, top=True, left=(side == 'left'))
            self._chrome.append(Deco(lcars, QtCore.QRect(sx, iy, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(lcars, QtCore.QRect(btn_x, iy, bw, bh), color))

        # Bottom corner: swish into the horizontal bar, or plain rect if no bottom bar
        if has_bot:
            svg = self._corner_svg(T, bh, t, bar, top=False, left=(side == 'left'))
            self._chrome.append(Deco(lcars, QtCore.QRect(sx, iy + ih - bh, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(lcars, QtCore.QRect(btn_x, iy + ih - bh, bw, bh), color))

    def _place_buttons(
        self,
        lcars: QtWidgets.QWidget,
        ix: int, iy: int, iw: int, ih: int,
        bh: int, bw: int, bs: int,
        upper: List[str],
        lower: List[str],
        side: str,
        has_sidebar: bool = True,
    ) -> None:
        """Create and register buttons for one sidebar."""
        if not upper and not lower and not has_sidebar:
            return
        btn_x = ix if side == 'left' else ix + iw - bw

        # Upper group — start below the top corner block (swish or plain rect)
        pos_y = iy + bh + bs
        for name in upper:
            self.buttons[name] = Bracket(
                lcars, QtCore.QRect(btn_x, pos_y, bw, bh), name + " ", self.color,
            )
            self.buttons[name].clicked.connect(
                partial(self.button_callback, button_name=name),
            )
            self._unbold(self.buttons[name])
            self.pages[name] = {}
            pos_y += bh + bs
        upper_end_y = pos_y

        # Lower group — packed above the bottom corner block (swish or plain rect)
        n_lower = len(lower)
        lower_gap = n_lower * (bh + bs) if n_lower > 0 else bs
        lower_start_y = iy + ih - bh - lower_gap
        for i, name in enumerate(lower):
            btn_y = lower_start_y + i * (bh + bs)
            self.buttons[name] = Bracket(
                lcars, QtCore.QRect(btn_x, btn_y, bw, bh), name + " ", self.color,
            )
            self.buttons[name].clicked.connect(
                partial(self.button_callback, button_name=name),
            )
            self._unbold(self.buttons[name])
            self.pages[name] = {}

        # Fill between groups
        fill_h = lower_start_y - upper_end_y
        if fill_h > 0 and has_sidebar:
            fill_x = ix if side == 'left' else ix + iw - bw
            fill = Block(lcars, QtCore.QRect(fill_x, upper_end_y, bw, fill_h), self.color)
            self._chrome.append(fill)

    @staticmethod
    def _corner_svg(T: int, bh: int, t: int, bar: int, top: bool, left: bool) -> str:
        """Return the SVG string for one swish corner piece.

        The four combinations of top/bottom × left/right are derived by
        mirroring the original Separator SVG horizontally and vertically.
        """
        if left and top:
            # Original Separator orientation=top
            return (
                f'<svg height="{bh}" width="{T}">'
                f'<circle cx="{t}" cy="{t}" r="{t}" fill="{{c}}" />'
                f'<rect x="0" y="{t}" width="{bar}" height="{t}" fill="{{c}}" />'
                f'<rect x="{t}" y="0" width="{T}" height="{t}" fill="{{c}}" />'
                f'<circle cx="{bar}" cy="{bh}" r="{t}" fill="#000" />'
                f'</svg>'
            )
        if left and not top:
            # Original Separator orientation=bottom
            return (
                f'<svg height="{bh}" width="{T}">'
                f'<circle cx="{t}" cy="{t}" r="{t}" fill="{{c}}" />'
                f'<rect x="0" y="0" width="{bar}" height="{t}" fill="{{c}}" />'
                f'<rect x="{t}" y="{t}" width="{T}" height="{t}" fill="{{c}}" />'
                f'<circle cx="{bar}" cy="0" r="{t}" fill="#000" />'
                f'</svg>'
            )
        if not left and top:
            # Horizontal mirror of left-top
            return (
                f'<svg height="{bh}" width="{T}">'
                f'<circle cx="{T - t}" cy="{t}" r="{t}" fill="{{c}}" />'
                f'<rect x="{T - bar}" y="{t}" width="{bar}" height="{t}" fill="{{c}}" />'
                f'<rect x="0" y="0" width="{T - t}" height="{t}" fill="{{c}}" />'
                f'<circle cx="{T - bar}" cy="{bh}" r="{t}" fill="#000" />'
                f'</svg>'
            )
        # not left and not top → horizontal mirror of left-bottom
        return (
            f'<svg height="{bh}" width="{T}">'
            f'<circle cx="{T - t}" cy="{t}" r="{t}" fill="{{c}}" />'
            f'<rect x="{T - bar}" y="0" width="{bar}" height="{t}" fill="{{c}}" />'
            f'<rect x="0" y="{t}" width="{T - t}" height="{t}" fill="{{c}}" />'
            f'<circle cx="{T - bar}" cy="0" r="{t}" fill="#000" />'
            f'</svg>'
        )

    @staticmethod
    def _make_cap(
        lcars: QtWidgets.QWidget, x: int, y: int, t: int, color: str, side: str,
    ) -> Deco:
        """Rounded end cap for a horizontal bar (left or right free end)."""
        r = t / 2
        if side == 'right':
            svg = (
                f'<svg height="{t}" width="{t}">'
                f'<rect x="0" y="0" width="{r}" height="{t}" fill="{{c}}" />'
                f'<circle cx="{r}" cy="{r}" r="{r}" fill="{{c}}" />'
                f'</svg>'
            )
        else:
            svg = (
                f'<svg height="{t}" width="{t}">'
                f'<rect x="{r}" y="0" width="{r}" height="{t}" fill="{{c}}" />'
                f'<circle cx="{r}" cy="{r}" r="{r}" fill="{{c}}" />'
                f'</svg>'
            )
        return Deco(lcars, QtCore.QRect(x, y, t, t), color, svg=svg)

    @staticmethod
    def _add_text(
        lcars: QtWidgets.QWidget,
        x_anchor: int,
        y: int,
        t: int,
        color: str,
        text: str,
        align_left: bool = False,
    ) -> Textline:
        """Text label cut into a bar, anchored near the left or right end."""
        font_size = max(8, int(t * 1.3))
        gap = 12
        text_w = (
            QtGui.QFontMetrics(QtGui.QFont("LCARS", font_size)).horizontalAdvance(text)
            + 16
        )
        text_x = (x_anchor + gap) if align_left else (x_anchor - gap - text_w)
        text_rect = QtCore.QRect(text_x, y, text_w, t)
        Block(lcars, text_rect, "#000000")
        label = Textline(lcars, text_rect, color, font_size)
        label.setText(text)
        label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)
        Frame._unbold(label)
        return label

    @staticmethod
    def _unbold(widget: QtWidgets.QWidget) -> None:
        f = widget.font()
        f.setBold(False)
        widget.setFont(f)
