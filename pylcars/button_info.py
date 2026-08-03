# -*- coding: utf-8 -*-
"""ButtonInfo: per-button customisation for Frame and SFrame sidebars."""
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class ButtonInfo:
    """Customisation for a single sidebar button.

    Attributes:
        name:   Button key.  Also the display text unless ``text`` is given.
        colour: Override colour for this button (uses frame color when None).
        height: Override height in pixels (uses default button height when None).
        text:   Display label, decoupling what is shown from the key used in
            ``Frame.buttons`` / ``SFrame.buttons`` and in button callbacks.
            Takes precedence over the frame's ``button_texts`` mapping.
            ``\\n`` starts a new line, and the button grows to fit.
    """
    name: str
    colour: Optional[str] = None
    height: Optional[int] = None
    text: Optional[str] = None


ButtonSpec = Union[str, ButtonInfo]


def _btn_name(spec: ButtonSpec) -> str:
    """Return the button's name/key from either a plain string or a ButtonInfo."""
    return spec.name if isinstance(spec, ButtonInfo) else spec
