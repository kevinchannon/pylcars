# -*- coding: utf-8 -*-
"""LCARS color scheme enumeration.

This module defines the official LCARS (Library Computer Access and Retrieval System)
color palette used throughout the interface. These colors represent the characteristic
80s-style aesthetic of the LCARS design system featured in Star Trek: The Next Generation.

The colors are defined as hex values and can be accessed as enumeration members.
"""

from .enumeration import Enumeration


class Colors(Enumeration):  # type: ignore
    """LCARS color palette enumeration.

    A complete set of colors used in the LCARS design system. Each color is named
    according to its characteristic appearance and is defined as a hexadecimal color value.
    """
    orange: str = '#f90'
    flieder: str = '#c9c'
    blaugrau: str = '#99c'
    rostbraun: str = '#c66'
    beige: str = '#fc9'
    leuchtblau: str = '#99f'
    apricot: str = '#f96'
    pink: str = '#c69'
    hellorange: str = '#fc4'
    rot: str = '#c00'
    yellow: str = '#dfce86'
    black: str = "#000"  # the LCARS background
    white: str = "#fff"  # brightest text
    silber: str = "#f0f0f0"  # body text; off-white
    grau: str = "#666"  # de-emphasised text
    anthrazit: str = "#3a3a3a"  # hairlines and rules
