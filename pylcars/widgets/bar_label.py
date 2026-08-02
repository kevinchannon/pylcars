"""Text label cut into a horizontal LCARS bar.

This module implements BarLabel, a Textline that owns the black block
masking the bar behind its text.  Label and mask are laid out together, so
changing the text keeps the mask exactly as wide as the text it hides.
"""
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from .block import Block
from .textline import Textline
from .. import config


class BarLabel(Textline):
    """A text label that cuts a black gap into a horizontal bar.

    The label is anchored near one end of the bar: with ``align_left`` it
    starts a fixed gap to the right of the anchor, otherwise it ends a fixed
    gap to the left of it.  The backing block is created before the label so
    the text stays on top of it.

    Attributes:
        backing: The black Block that masks the bar behind the text.
    """
    backing: Block

    def __init__(
        self,
        lcars: QtWidgets.QWidget,
        x_anchor: int,
        y: int,
        t: int,
        color: str,
        font_size: int,
        align_left: bool = False,
        gap: int = 12,
        padding_chars: float = 3.0,
        letter_spacing: Optional[int] = None,
    ) -> None:
        """Initialise a BarLabel.

        Args:
            lcars: Parent LCARS window.
            x_anchor: Bar end the text is anchored to (left end when
                ``align_left``, right end otherwise).
            y: Top of the bar.
            t: Bar thickness (px).
            color: Text color.
            font_size: Font size in points.
            align_left: Anchor to the left end of the bar instead of the right.
            gap: Distance between the anchor and the near edge of the gap (px).
            padding_chars: Total horizontal padding around the text, in
                multiples of the width of a capital "I".
            letter_spacing: Absolute letter spacing in px, or None for none.
        """
        self._x_anchor = x_anchor
        self._bar_y = y
        self._bar_t = t
        self._align_left = align_left
        self._gap = gap
        self._padding_chars = padding_chars
        self._bar_font = QtGui.QFont(config.DEFAULT_FONT_NAME, font_size)
        if letter_spacing is not None:
            self._bar_font.setLetterSpacing(QtGui.QFont.AbsoluteSpacing, letter_spacing)
        fm = QtGui.QFontMetrics(self._bar_font)
        self._bar_fm = fm
        self._widget_h = fm.height()
        self._widget_y = y + t // 2 - fm.ascent() + fm.capHeight() // 2

        self.backing = Block(lcars, QtCore.QRect(x_anchor, y, 1, t), "#000000")
        Textline.__init__(
            self,
            lcars,
            QtCore.QRect(x_anchor, self._widget_y, 1, self._widget_h),
            color,
            font_size,
        )
        self.setStyleSheet(f"background: transparent; color: {color}; border: none;")
        self._bar_font.setBold(False)
        self.setFont(self._bar_font)
        self.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter)

    def setText(self, text: Optional[str]) -> None:
        """Set the label text and resize the backing block to match it.

        Args:
            text: New text to display.
        """
        self._relayout(text or "")
        Textline.setText(self, text)

    def text_width(self, text: str) -> int:
        """Return the width of the gap needed to show ``text``.

        Args:
            text: Text to measure.

        Returns:
            Width in pixels, including the padding either side of the text.
        """
        fm = self._bar_fm
        padding = int(self._padding_chars * fm.tightBoundingRect("I").width())
        return fm.horizontalAdvance(text) + padding

    def _relayout(self, text: str) -> None:
        """Reposition and resize the label and its backing block for ``text``."""
        text_w = self.text_width(text)
        text_x = (
            self._x_anchor + self._gap
            if self._align_left
            else self._x_anchor - self._gap - text_w
        )
        self.backing.set_rect(QtCore.QRect(text_x, self._bar_y, text_w, self._bar_t))
        self.set_rect(QtCore.QRect(text_x, self._widget_y, text_w, self._widget_h))
