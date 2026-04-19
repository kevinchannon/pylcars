# -*- coding: utf-8 -*-
"""FrameBorder enumeration for LCARS frame widgets."""
from enum import Enum, auto


class FrameBorder(Enum):
    """Which sides of an LCARS frame are visible.

    Combine any subset as a ``set[FrameBorder]`` and pass to ``Frame``.
    Common presets expressed as border codes::

        C-Style  : {TOP, BOTTOM, LEFT}   (TBL)
        D-Style  : {TOP, BOTTOM, RIGHT}  (TBR)
        N-Style  : {TOP, LEFT, RIGHT}    (TLR)
        U-Style  : {BOTTOM, LEFT, RIGHT} (BLR)
        O-Style  : {TOP, BOTTOM, LEFT, RIGHT}
        R-Style  : {TOP, LEFT}
        L-Style  : {BOTTOM, LEFT}
        Header   : {TOP}
        Footer   : {BOTTOM}
        Left I   : {LEFT}
        Right I  : {RIGHT}
    """
    TOP = auto()
    BOTTOM = auto()
    LEFT = auto()
    RIGHT = auto()
