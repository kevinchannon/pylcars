# -*- coding: utf-8 -*-
"""ButtonInfo: per-button customisation for Frame and SFrame sidebars."""
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class ButtonInfo:
    """Customisation for a single sidebar button.

    Attributes:
        name:   Button key and default display text.
        colour: Override colour for this button (uses frame color when None).
        height: Override height in pixels (uses default button height when None).
    """
    name: str
    colour: Optional[str] = None
    height: Optional[int] = None


ButtonSpec = Union[str, ButtonInfo]


def _btn_name(spec: ButtonSpec) -> str:
    """Return the button's name/key from either a plain string or a ButtonInfo."""
    return spec.name if isinstance(spec, ButtonInfo) else spec
