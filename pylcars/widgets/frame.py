# -*- coding: utf-8 -*-
"""Generic LCARS frame widget driven by a set of visible borders."""
from typing import Any, Callable, Dict, List, Optional, Set, Union

from PyQt5 import QtCore, QtGui, QtWidgets

from .bar_label import BarLabel
from .block import Block
from .bracket import Bracket
from .deco import Deco
from .frame_support import (
    MIN_BUTTON_HEIGHT,
    SidebarButtons,
    check_button_names,
    resolve_play_sound,
    set_font_size,
    unbold,
)
from .separator import Separator
from ..conditions import Conditions
from .. import config
from ..frame_border import FrameBorder
from ..orientation import Orientation
from ..button_info import ButtonSpec, _btn_name


def _cap_height(fm: QtGui.QFontMetrics) -> int:
    return fm.capHeight()


def points_for_height(family: str, target_px: int) -> int:
    """Return the largest point size whose cap height does not exceed target_px."""
    lo, hi = 4, 200
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _cap_height(QtGui.QFontMetrics(QtGui.QFont(family, mid))) <= target_px:
            lo = mid
        else:
            hi = mid - 1
    return lo


def bar_thickness(thin_thickness: int) -> int:
    """Return the bar thickness a frame actually uses for a requested thickness.

    The request is round-tripped through the label font: the result is the cap
    height of the largest point size that fits inside ``thin_thickness``, so a
    bar is exactly as tall as the text it can hold.  That makes it ``<=``
    the requested value.  Frame and SFrame both derive their thickness this
    way, so the same ``thin_thickness`` lines up across the two.

    Args:
        thin_thickness: Requested bar thickness in pixels.

    Returns:
        The bar thickness in pixels.
    """
    font_points = points_for_height(config.DEFAULT_FONT_NAME, thin_thickness)
    return QtGui.QFontMetrics(QtGui.QFont(config.DEFAULT_FONT_NAME, font_points)).capHeight()


class Frame(SidebarButtons):
    """LCARS frame whose visible borders are selected via a set of FrameBorder values.

    Each visible sidebar (LEFT / RIGHT) may carry an upper and lower button
    group.  Clicking any button hides the previous page and shows the new one,
    matching the behaviour of Menue.

    Button names are keys, not labels: they must be unique across the whole
    frame, and the label is set separately with ``ButtonInfo.text`` or
    ``button_texts`` and changed later with
    :meth:`~pylcars.widgets.frame_support.SidebarButtons.set_button_text`.

    Attributes:
        buttons: All button widgets keyed by name.
        pages: Content widget dicts keyed by button name.
        fields: All button names in order (left-upper, left-lower,
            right-upper, right-lower).
        active_page: Name of the currently visible page.
        enabled: Whether button interaction is active.
        color: Primary frame color.
        color_active: Color for the active button.
        parent: Widget the frame is built on.
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
        self._play_sound()
        self.blend_out(self.active_page)
        self.buttons[self.active_page].tockle()
        self.active_page = button_name
        self.buttons[self.active_page].tockle(self._active_color(self.active_page))
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
        parent: QtWidgets.QWidget,
        rect: QtCore.QRect,
        borders: Set[FrameBorder],
        left_upper_buttons: Optional[List[ButtonSpec]] = None,
        left_lower_buttons: Optional[List[ButtonSpec]] = None,
        right_upper_buttons: Optional[List[ButtonSpec]] = None,
        right_lower_buttons: Optional[List[ButtonSpec]] = None,
        padding: int = 4,
        thin_thickness: int = 20,
        thick_thickness: int = 200,
        button_spacing: int = 4,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        color: str = Conditions.use,
        color_active: str = Conditions.active,
        button_callback: Optional[Callable[[str], None]] = None,
        button_texts: Optional[Dict[str, str]] = None,
        button_font_size: Optional[int] = None,
        play_sound: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialise a Frame.

        Args:
            parent: Widget the frame is built on.  Any QWidget will do — an
                Lcars window, or a plain container so the frame can be shown,
                hidden and moved as one object.
            rect: Bounding rectangle for the entire frame.
            borders: Set of FrameBorder values selecting which sides are drawn.
            left_upper_buttons: Buttons for the top of the left sidebar (str or ButtonInfo).
            left_lower_buttons: Buttons for the bottom of the left sidebar (str or ButtonInfo).
            right_upper_buttons: Buttons for the top of the right sidebar (str or ButtonInfo).
            right_lower_buttons: Buttons for the bottom of the right sidebar (str or ButtonInfo).
            padding: Gap between bounding rect and frame chrome (px).
            thin_thickness: Height of the horizontal bars (px).
            thick_thickness: Total width of each sidebar (px).
            button_spacing: Gap between consecutive chrome elements (px).
            header_text: Optional label on the top bar.
            footer_text: Optional label on the bottom bar.
            color: Primary frame color.
            color_active: Color for the active button.
            button_callback: Override for the default page-switch handler.
            button_texts: Display labels keyed by button name, for buttons whose
                label should differ from their key.  ``ButtonInfo.text`` wins
                where both are given.
            button_font_size: Point size for sidebar button text. When ``None``
                (default) the Bracket default font size is used.
            play_sound: Called on each page switch.  When ``None`` (default) the
                parent's ``play_sound`` is used if it has one, and the frame is
                silent otherwise.

        Raises:
            ValueError: If a button name is used more than once.
        """
        left_upper_buttons = left_upper_buttons or []
        left_lower_buttons = left_lower_buttons or []
        right_upper_buttons = right_upper_buttons or []
        right_lower_buttons = right_lower_buttons or []

        check_button_names(
            left_upper_buttons, left_lower_buttons, right_upper_buttons, right_lower_buttons,
        )

        self.parent = parent
        self.color = color
        self.color_active = color_active
        self._play_sound = resolve_play_sound(parent, play_sound)
        self.enabled = True
        self._header_label: Optional[BarLabel] = None
        self._footer_label: Optional[BarLabel] = None
        self._chrome: list = []

        has_top = FrameBorder.TOP in borders
        has_bot = FrameBorder.BOTTOM in borders
        has_left = FrameBorder.LEFT in borders
        has_right = FrameBorder.RIGHT in borders

        t = bar_thickness(thin_thickness)
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
                parent, ix, iy, iw, ih,
                T, bh, bw, bar, t, bs, color,
                side='left', has_top=has_top, has_bot=has_bot,
            )

        # ── Right sidebar ─────────────────────────────────────────────────
        if has_right:
            self._build_sidebar(
                parent, ix, iy, iw, ih,
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
            top_bar = Block(parent, QtCore.QRect(bar_left, iy, bar_w, t), color)
            self._chrome.append(top_bar)
            if not has_left:
                self._chrome.append(self._make_cap(parent, bar_left, iy, t, color, side='left'))
            if not has_right:
                self._chrome.append(self._make_cap(parent, bar_right_x - t, iy, t, color, side='right'))
            if header_text is not None:
                self._header_label = self._add_text(
                    parent, text_x_anchor, iy, t, color, header_text, align_left=align_left,
                )

        if has_bot:
            bot_y = iy + ih - t
            bot_bar = Block(parent, QtCore.QRect(bar_left, bot_y, bar_w, t), color)
            self._chrome.append(bot_bar)
            if not has_left:
                self._chrome.append(self._make_cap(parent, bar_left, bot_y, t, color, side='left'))
            if not has_right:
                self._chrome.append(self._make_cap(parent, bar_right_x - t, bot_y, t, color, side='right'))
            if footer_text is not None:
                self._footer_label = self._add_text(
                    parent, text_x_anchor, bot_y, t, color, footer_text, align_left=align_left,
                )

        # ── Display rect ──────────────────────────────────────────────────
        has_any_bar = has_top or has_bot
        if has_left or has_right:
            display_y = iy + (bh + bs if has_any_bar else 0)
            display_bot = iy + ih - (bh if has_any_bar else 0)
        elif has_top:
            display_y = iy + t + bs
            display_bot = iy + ih - (t if has_bot else 0)
        else:
            display_y = iy
            display_bot = iy + ih - (t if has_bot else 0)

        display_x = ix + (T + bs if has_left else (t if has_any_bar else 0))
        display_right = ix + iw - (T + bs if has_right else (t if has_any_bar else 0))

        self._display_rect = QtCore.QRect(
            display_x,
            display_y,
            display_right - display_x,
            display_bot - display_y,
        )

        # ── Buttons ───────────────────────────────────────────────────────
        self._init_buttons(
            button_texts=button_texts,
            button_font_size=button_font_size,
            min_button_height=max(MIN_BUTTON_HEIGHT, bh),
        )
        self.pages = {}
        self.fields = (
            [_btn_name(s) for s in left_upper_buttons] + [_btn_name(s) for s in left_lower_buttons]
            + [_btn_name(s) for s in right_upper_buttons] + [_btn_name(s) for s in right_lower_buttons]
        )
        self.button_callback = button_callback or self.frame_click

        # One column per sidebar: upper group from the top corner down, lower
        # group packed against the bottom corner, filler block between them.
        self._add_button_column(
            parent, self._chrome,
            x=ix, w=bw,
            top_y=iy + bh + bs, bot_y=iy + ih - bh, spacing=bs,
            callback=self.button_callback, pages=self.pages,
            top_group=left_upper_buttons, bottom_group=left_lower_buttons, side='left',
            fill=has_left, fill_bottom_gap=bs,
        )
        self._add_button_column(
            parent, self._chrome,
            x=ix + iw - bw, w=bw,
            top_y=iy + bh + bs, bot_y=iy + ih - bh, spacing=bs,
            callback=self.button_callback, pages=self.pages,
            top_group=right_upper_buttons, bottom_group=right_lower_buttons, side='right',
            fill=has_right, fill_bottom_gap=bs,
        )

        if self.fields:
            self.active_page = self.fields[0]
            self.buttons[self.active_page].tockle(self._active_color(self.active_page))
        else:
            self.active_page = ""

    # ── Private geometry helpers ──────────────────────────────────────────

    def _build_sidebar(
        self,
        parent: QtWidgets.QWidget,
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
            self._chrome.append(Deco(parent, QtCore.QRect(sx, iy, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(parent, QtCore.QRect(btn_x, iy, bw, bh), color))

        # Bottom corner: swish into the horizontal bar, or plain rect if no bottom bar
        if has_bot:
            svg = self._corner_svg(T, bh, t, bar, top=False, left=(side == 'left'))
            self._chrome.append(Deco(parent, QtCore.QRect(sx, iy + ih - bh, T, bh), color, svg=svg))
        else:
            self._chrome.append(Block(parent, QtCore.QRect(btn_x, iy + ih - bh, bw, bh), color))

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
        parent: QtWidgets.QWidget, x: int, y: int, t: int, color: str, side: str,
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
        return Deco(parent, QtCore.QRect(x, y, t, t), color, svg=svg)

    @staticmethod
    def _add_text(
        parent: QtWidgets.QWidget,
        x_anchor: int,
        y: int,
        t: int,
        color: str,
        text: str,
        align_left: bool = False,
    ) -> BarLabel:
        """Text label cut into a bar, anchored near the left or right end."""
        font_size = points_for_height(config.DEFAULT_FONT_NAME, t)
        label = BarLabel(parent, x_anchor, y, t, color, font_size, align_left=align_left)
        label.setText(text)
        return label

    _unbold = staticmethod(unbold)
    _set_font_size = staticmethod(set_font_size)
