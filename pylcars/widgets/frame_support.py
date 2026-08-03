# -*- coding: utf-8 -*-
"""Plumbing shared by :class:`Frame` and :class:`SFrame`.

The two frame classes present the same button vocabulary to callers — the same
``buttons`` dict, the same ``ButtonSpec`` lists, the same colour and sizing
rules — so everything about *what a sidebar button is* lives here.  That leaves
the frame classes deciding only *where* a column of buttons goes, which is
their real difference.
"""
from dataclasses import dataclass, field
from functools import partial
from typing import Any, Callable, Dict, List, Optional, Sequence, Set, Tuple, cast

from PyQt5 import QtCore, QtWidgets

from .block import Block
from .bracket import Bracket
from ..button_info import ButtonInfo, ButtonSpec, _btn_name

MIN_BUTTON_HEIGHT: int = 30
"""Floor applied to the height of a single-line sidebar button, in pixels."""


def _silent() -> None:
    """No-op sound handler used by frames with no audio source."""


def resolve_play_sound(
    parent: QtWidgets.QWidget,
    play_sound: Optional[Callable[[], None]],
) -> Callable[[], None]:
    """Return the click sound handler for a frame.

    An explicitly injected handler wins.  Failing that the parent widget is
    asked for one, which keeps frames parented to an :class:`~pylcars.Lcars`
    window audible without any code change.  A frame parented to a plain
    container with no handler is silent rather than broken.

    Args:
        parent: Parent widget the frame was built on.
        play_sound: Handler supplied by the caller, if any.

    Returns:
        A callable taking no arguments.
    """
    if play_sound is not None:
        return play_sound
    inherited = getattr(parent, "play_sound", None)
    if callable(inherited):
        return cast(Callable[[], None], inherited)
    return _silent


def check_button_names(*groups: Optional[Sequence[ButtonSpec]]) -> None:
    """Raise if a button name is used more than once across *groups*.

    A frame keys every button group into one ``buttons`` dict, so a repeated
    name would leave one widget on screen but unreachable, firing its callback
    under the wrong key.

    Args:
        *groups: Button spec lists, in construction order.  ``None`` is allowed.

    Raises:
        ValueError: If any name appears in more than one place.
    """
    seen: Set[str] = set()
    duplicates: List[str] = []
    for group in groups:
        for spec in group or ():
            name = _btn_name(spec)
            if name in seen and name not in duplicates:
                duplicates.append(name)
            seen.add(name)
    if duplicates:
        raise ValueError(_duplicate_message(duplicates))


def _duplicate_message(names: Sequence[str]) -> str:
    listed = ", ".join(repr(n) for n in names)
    return (
        f"duplicate button name(s): {listed}. Button names are the keys of "
        "Frame.buttons / SFrame.buttons and must be unique across the whole "
        "frame. To show the same label twice, give the buttons distinct names "
        "and set the label with ButtonInfo(name=..., text=...)."
    )


def button_style(side: str) -> str:
    """Return the Bracket stylesheet for a button on the given sidebar."""
    align_left = side == 'right'
    return Bracket.default_style.replace(
        "Text-align: top right;",
        "Text-align: top left;" if align_left else "Text-align: top right;",
    )


def unbold(widget: QtWidgets.QWidget) -> None:
    """Clear the bold flag on a widget's font."""
    f = widget.font()
    f.setBold(False)
    widget.setFont(f)


def set_font_size(widget: QtWidgets.QWidget, size: int) -> None:
    """Set a widget's font point size."""
    f = widget.font()
    f.setPointSize(size)
    widget.setFont(f)


@dataclass
class _Resolved:
    """A button spec reduced to the values needed to build the widget."""
    name: str
    text: str
    colour: str


@dataclass
class _ButtonColumn:
    """One vertical run of sidebar buttons, and how to (re-)lay it out.

    ``top_group`` flows down from ``top_y``; ``bottom_group`` is packed up
    against ``bot_y``.  Whatever is left between them is filled with a Block,
    stopping ``fill_bottom_gap`` pixels short of what follows it.
    """
    parent: QtWidgets.QWidget
    chrome: List[Any]
    x: int
    w: int
    top_y: int
    bot_y: int
    spacing: int
    fill_bottom_gap: int
    wants_fill: bool
    top_group: List[str] = field(default_factory=list)
    bottom_group: List[str] = field(default_factory=list)
    fill: Optional[Block] = None


class SidebarButtons:
    """Mixin owning sidebar button creation, sizing and relabelling.

    A frame class calls :meth:`_init_buttons` once, then
    :meth:`_add_button_column` for each vertical run of buttons it lays out.

    Attributes:
        buttons: All button widgets keyed by name.
    """

    buttons: Dict[str, Bracket]
    color: str
    color_active: str

    # ── Public API ────────────────────────────────────────────────────────

    def set_button_text(self, name: str, text: str) -> None:
        """Change a button's label without changing its key.

        The button keeps its key in :attr:`buttons`, so callbacks that switch
        on the button name keep working across a relabel.  A label that gains
        or loses a line changes the button's height (unless it was created with
        an explicit ``ButtonInfo.height``) and the rest of the column is
        re-flowed to match.

        Args:
            name: Button key, as given at construction.
            text: New display text; ``\\n`` starts a new line.

        Raises:
            KeyError: If the frame has no button with that name.
        """
        if name not in self.buttons:
            raise KeyError(f"no button named {name!r}")
        self.buttons[name].setText(text)
        self._display_texts[name] = text
        column = self._column_of.get(name)
        if column is not None:
            self._layout_column(column)

    def button_text(self, name: str) -> str:
        """Return a button's current display text.

        Args:
            name: Button key, as given at construction.

        Raises:
            KeyError: If the frame has no button with that name.
        """
        if name not in self.buttons:
            raise KeyError(f"no button named {name!r}")
        return self._display_texts[name]

    # ── Set-up ────────────────────────────────────────────────────────────

    def _init_buttons(
        self,
        button_texts: Optional[Dict[str, str]] = None,
        button_font_size: Optional[int] = None,
        min_button_height: int = MIN_BUTTON_HEIGHT,
    ) -> None:
        """Prepare button bookkeeping.  Call before any :meth:`_add_button_column`."""
        self.buttons = {}
        self._button_texts: Dict[str, str] = dict(button_texts or {})
        self._button_font_size = button_font_size
        self._min_button_height = min_button_height
        self._explicit_colour_buttons: Set[str] = set()
        self._display_texts: Dict[str, str] = {}
        self._fixed_heights: Dict[str, Optional[int]] = {}
        self._columns: List[_ButtonColumn] = []
        self._column_of: Dict[str, _ButtonColumn] = {}

    def _add_button_column(
        self,
        parent: QtWidgets.QWidget,
        chrome: List[Any],
        x: int,
        w: int,
        top_y: int,
        bot_y: int,
        spacing: int,
        callback: Callable[..., None],
        pages: Dict[str, Dict[str, Any]],
        top_group: Sequence[ButtonSpec] = (),
        bottom_group: Sequence[ButtonSpec] = (),
        side: str = 'left',
        fill: bool = True,
        fill_bottom_gap: int = 0,
    ) -> None:
        """Create one column of sidebar buttons and its filler block.

        Args:
            parent: Widget the buttons are parented to.
            chrome: Frame's chrome list; the filler block is appended to it.
            x: Left edge of the column.
            w: Button width.
            top_y: Top of the space the column may use.
            bot_y: Bottom of the space the column may use.
            spacing: Gap between consecutive buttons.
            callback: Click handler, called with ``button_name=<name>``.
            pages: Page dict to register each button's (empty) page in.
            top_group: Buttons flowing down from ``top_y``.
            bottom_group: Buttons packed up against ``bot_y``.
            side: ``'left'`` or ``'right'``; selects text alignment.
            fill: Whether to fill the gap left over with a Block.
            fill_bottom_gap: Pixels of clearance between the filler block and
                whatever sits below it.

        Raises:
            ValueError: If a button name is already in use on this frame.
        """
        column = _ButtonColumn(
            parent=parent,
            chrome=chrome,
            x=x,
            w=w,
            top_y=top_y,
            bot_y=bot_y,
            spacing=spacing,
            fill_bottom_gap=fill_bottom_gap,
            wants_fill=fill,
            top_group=[_btn_name(s) for s in top_group],
            bottom_group=[_btn_name(s) for s in bottom_group],
        )
        resolved = [self._resolve(spec) for spec in list(top_group) + list(bottom_group)]
        for entry in resolved:
            self._column_of[entry.name] = column
        self._columns.append(column)

        rects, fill_rect = self._column_geometry(column)
        style = button_style(side)
        for entry in resolved:
            self._create_button(parent, entry, rects[entry.name], style, callback, pages)
        self._set_fill(column, fill_rect)

    # ── Colour ────────────────────────────────────────────────────────────

    def _active_color(self, button_name: str) -> str:
        """Return the colour to use when a button becomes the active page.

        Buttons created with an explicit ``ButtonInfo.colour`` keep that colour
        in both active and inactive states (they are decorative / informational).
        Plain buttons use ``color_active``, the standard LCARS navigation
        highlight.
        """
        if button_name in self._explicit_colour_buttons:
            return self.buttons[button_name].color
        return self.color_active

    # ── Private helpers ───────────────────────────────────────────────────

    def _resolve(self, spec: ButtonSpec) -> _Resolved:
        """Reduce a spec to name/text/colour, recording its sizing information.

        ``ButtonInfo.text`` wins over the frame's ``button_texts`` mapping,
        which in turn wins over using the name as the label.
        """
        name = _btn_name(spec)
        if name in self._display_texts:
            raise ValueError(_duplicate_message([name]))
        info = spec if isinstance(spec, ButtonInfo) else None

        if info is not None and info.text is not None:
            text = info.text
        else:
            text = self._button_texts.get(name, name)

        colour = self.color
        if info is not None and info.colour is not None:
            colour = info.colour
            self._explicit_colour_buttons.add(name)

        self._display_texts[name] = text
        self._fixed_heights[name] = info.height if info is not None else None
        return _Resolved(name=name, text=text, colour=colour)

    def _button_height(self, name: str) -> int:
        """Return a button's height: its fixed height, or one row per text line."""
        fixed = self._fixed_heights.get(name)
        if fixed is not None:
            return fixed
        return self._min_button_height * (self._display_texts[name].count('\n') + 1)

    def _column_geometry(
        self, column: _ButtonColumn,
    ) -> Tuple[Dict[str, QtCore.QRect], Optional[QtCore.QRect]]:
        """Return button rects keyed by name, plus the filler rect if any."""
        bs = column.spacing
        rects: Dict[str, QtCore.QRect] = {}

        pos_y = column.top_y
        for name in column.top_group:
            height = self._button_height(name)
            rects[name] = QtCore.QRect(column.x, pos_y, column.w, height)
            pos_y += height + bs
        upper_end_y = pos_y

        if column.bottom_group:
            heights = [self._button_height(name) for name in column.bottom_group]
            # Packed against bot_y, leaving one spacing below the last button.
            lower_start_y = max(upper_end_y + bs, column.bot_y - sum(heights) - len(heights) * bs)
            pos_y = lower_start_y
            for name, height in zip(column.bottom_group, heights):
                rects[name] = QtCore.QRect(column.x, pos_y, column.w, height)
                pos_y += height + bs
            fill_bot_y = lower_start_y - column.fill_bottom_gap
        else:
            fill_bot_y = column.bot_y - column.fill_bottom_gap

        fill_rect = None
        if column.wants_fill and fill_bot_y > upper_end_y:
            fill_rect = QtCore.QRect(column.x, upper_end_y, column.w, fill_bot_y - upper_end_y)
        return rects, fill_rect

    def _layout_column(self, column: _ButtonColumn) -> None:
        """Re-apply a column's geometry to widgets that already exist."""
        rects, fill_rect = self._column_geometry(column)
        for name, rect in rects.items():
            button = self.buttons[name]
            button.rect = rect
            button.setGeometry(rect)
        self._set_fill(column, fill_rect)

    def _set_fill(self, column: _ButtonColumn, rect: Optional[QtCore.QRect]) -> None:
        """Create, resize or hide a column's filler block."""
        if rect is None:
            if column.fill is not None:
                column.fill.hide()
            return
        if column.fill is None:
            column.fill = Block(column.parent, rect, self.color)
            column.chrome.append(column.fill)
            return
        column.fill.rect = rect
        column.fill.setGeometry(rect)
        column.fill.paint_back(column.fill.color)
        column.fill.show()

    def _create_button(
        self,
        parent: QtWidgets.QWidget,
        entry: _Resolved,
        rect: QtCore.QRect,
        style: str,
        callback: Callable[..., None],
        pages: Dict[str, Dict[str, Any]],
    ) -> None:
        """Build one Bracket, wire its callback and register its page."""
        button = Bracket(parent, rect, entry.text, entry.colour, style=style)
        button.clicked.connect(partial(callback, button_name=entry.name))
        unbold(button)
        if self._button_font_size is not None:
            set_font_size(button, self._button_font_size)
        self.buttons[entry.name] = button
        pages[entry.name] = {}
