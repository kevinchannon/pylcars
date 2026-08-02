"""PyLCARS - LCARS Interface Library for PyQt5.

A Python library for creating LCARS (Library Computer Access and Retrieval System)
style user interfaces using PyQt5. Provides a complete set of widgets, colors,
and styling consistent with the iconic interface design from Star Trek: The Next Generation.

This package includes:
- Core enumeration and condition systems
- LCARS color scheme definitions
- Widget classes for building interfaces (buttons, sliders, menus, etc.)
- SVG rendering and caching for complex shapes
- Audio playback support
- Complete main window class for LCARS applications
"""

from .lcars import Lcars
from .enumeration import Enumeration
from .conditions import Conditions
from .colors import Colors
from .orientation import Orientation
from .widgets.semicircle import Semicircle
from .widgets.deco import Deco
from .widgets.block import Block
from .widgets.separator import Separator
from .widgets.bracket import Bracket
from .widgets.menue import Menue
from .widgets.frame import Frame, points_for_height
from .widgets.s_frame import SFrame
from .button_info import ButtonInfo
from .frame_border import FrameBorder
from .widgets.updown import Updown
from .widgets.layout_grid import LayoutGrid
from .widgets.slider import Slider
from .widgets.textline import Textline
from .widgets.bar_label import BarLabel
from .widgets.plot import Plot
from .widgets.linear_gauge import LinearGauge, GaugeConfig, ZoneInterval
from .widgets.split_pill import SplitPill, SplitPillStyles
from .color_range import color_for_value
from .sound import Sound
from . import config


def set_font(name: str) -> None:
    """Override the default font used by all pylcars widgets.

    Call this before creating any widgets, after loading the font with
    QFontDatabase.addApplicationFont().
    """
    config.DEFAULT_FONT_NAME = name


__all__ = [
    "Lcars",
    "Enumeration",
    "Conditions",
    "Colors",
    "Orientation",
    "Semicircle",
    "Deco",
    "Block",
    "Separator",
    "Bracket",
    "Menue",
    "Frame",
    "points_for_height",
    "SFrame",
    "ButtonInfo",
    "FrameBorder",
    "Updown",
    "LayoutGrid",
    "Slider",
    "Textline",
    "BarLabel",
    "Plot",
    "LinearGauge",
    "GaugeConfig",
    "ZoneInterval",
    "Sound",
    "SplitPill",
    "SplitPillStyles",
    "color_for_value",
    "set_font",
    "config",
]
