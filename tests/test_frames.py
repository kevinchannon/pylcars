# -*- coding: utf-8 -*-
"""Tests for Frame / SFrame button behaviour and the parity between them."""
import pytest
from PyQt5 import QtCore, QtWidgets

from pylcars import ButtonInfo, Colors, Frame, FrameBorder, SFrame, bar_thickness

RECT = QtCore.QRect(0, 0, 800, 480)
LEFT_FRAME_BORDERS = {FrameBorder.TOP, FrameBorder.BOTTOM, FrameBorder.LEFT}

pytestmark = pytest.mark.gui


@pytest.fixture
def container(qapp: QtWidgets.QApplication) -> QtWidgets.QWidget:
    """A plain parent widget with no ``play_sound`` of its own."""
    widget = QtWidgets.QWidget()
    widget.resize(800, 480)
    return widget


def make_frame(parent, **kwargs) -> Frame:
    kwargs.setdefault("borders", LEFT_FRAME_BORDERS)
    return Frame(parent, RECT, **kwargs)


def make_s_frame(parent, **kwargs) -> SFrame:
    return SFrame(parent, RECT, **kwargs)


# ── Labels decoupled from keys ────────────────────────────────────────────

def test_button_info_text_sets_label_without_changing_key(container):
    frame = make_s_frame(container, upper_buttons=[ButtonInfo("week_toggle", text="LIST VIEW")])
    assert "week_toggle" in frame.buttons
    assert frame.buttons["week_toggle"].text() == "LIST VIEW"


def test_button_texts_maps_key_to_label_in_both_classes(container):
    frame = make_frame(container, left_upper_buttons=["a"], button_texts={"a": "ALPHA"})
    s_frame = make_s_frame(container, upper_buttons=["a"], button_texts={"a": "ALPHA"})
    assert frame.buttons["a"].text() == "ALPHA"
    assert s_frame.buttons["a"].text() == "ALPHA"


@pytest.mark.parametrize("factory, group", [
    (make_frame, "left_upper_buttons"),
    (make_s_frame, "upper_buttons"),
])
def test_button_info_text_beats_button_texts(container, factory, group):
    frame = factory(
        container,
        **{group: [ButtonInfo("a", text="FROM INFO")]},
        button_texts={"a": "FROM MAP"},
    )
    assert frame.buttons["a"].text() == "FROM INFO"


def test_same_label_may_appear_in_both_halves_of_an_s_frame(container):
    frame = make_s_frame(
        container,
        upper_buttons=[ButtonInfo("week_toggle", text="TOGGLE VIEW")],
        lower_buttons=[ButtonInfo("month_toggle", text="TOGGLE VIEW")],
    )
    assert frame.buttons["week_toggle"].text() == "TOGGLE VIEW"
    assert frame.buttons["month_toggle"].text() == "TOGGLE VIEW"
    assert frame.buttons["week_toggle"] is not frame.buttons["month_toggle"]


# ── Duplicate names ───────────────────────────────────────────────────────

def test_s_frame_rejects_a_name_used_in_both_halves(container):
    with pytest.raises(ValueError, match="duplicate button name"):
        make_s_frame(container, upper_buttons=["SAME"], lower_buttons=["SAME"])


def test_frame_rejects_a_name_used_in_two_groups(container):
    with pytest.raises(ValueError, match="duplicate button name"):
        make_frame(container, left_upper_buttons=["SAME"], left_lower_buttons=["SAME"])


def test_frame_rejects_a_name_repeated_within_one_group(container):
    with pytest.raises(ValueError, match="duplicate button name"):
        make_frame(container, left_upper_buttons=["SAME", ButtonInfo("SAME")])


# ── Sizing parity ─────────────────────────────────────────────────────────

def test_multi_line_labels_are_the_same_height_in_both_classes(container):
    frame = make_frame(container, left_upper_buttons=["ONE", "TWO\nLINES"])
    s_frame = make_s_frame(container, upper_buttons=["ONE", "TWO\nLINES"])

    single = frame.buttons["ONE"].geometry().height()
    assert frame.buttons["TWO\nLINES"].geometry().height() == 2 * single
    assert s_frame.buttons["ONE"].geometry().height() == single
    assert s_frame.buttons["TWO\nLINES"].geometry().height() == 2 * single


def test_multi_line_label_from_button_texts_also_grows(container):
    frame = make_s_frame(
        container, upper_buttons=["a", "b"], button_texts={"b": "TWO\nLINES"},
    )
    assert (frame.buttons["b"].geometry().height()
            == 2 * frame.buttons["a"].geometry().height())


def test_explicit_height_wins_over_line_count(container):
    frame = make_s_frame(container, upper_buttons=[ButtonInfo("a", height=52, text="TWO\nLINES")])
    assert frame.buttons["a"].geometry().height() == 52


def test_thin_buttons_hit_the_same_minimum_height_in_both_classes(container):
    frame = make_frame(container, left_upper_buttons=["a"], thin_thickness=6)
    s_frame = make_s_frame(container, upper_buttons=["a"], thin_thickness=6)
    height = frame.buttons["a"].geometry().height()
    assert height == 30
    assert s_frame.buttons["a"].geometry().height() == height


def test_both_classes_derive_the_same_bar_thickness(container):
    """The sidebar corner pieces line up when both are given one thin_thickness.

    Both classes round-trip ``thin_thickness`` through the label font, so the
    top corner piece is ``2 * bar_thickness()`` tall in each and the first
    button sits directly below it.
    """
    padding, spacing = 4, 4
    expected_top = padding + 2 * bar_thickness(20) + spacing

    frame = make_frame(
        container, left_upper_buttons=["a"], thin_thickness=20,
        padding=padding, button_spacing=spacing,
    )
    s_frame = make_s_frame(
        container, upper_buttons=["a"], thin_thickness=20,
        padding=padding, button_spacing=spacing,
    )
    assert frame.buttons["a"].geometry().top() == expected_top
    assert s_frame.buttons["a"].geometry().top() == expected_top


def test_bar_thickness_never_exceeds_the_request(qapp):
    for requested in (6, 12, 20, 33):
        assert bar_thickness(requested) <= requested


def test_button_font_size_applies_in_both_classes(container):
    frame = make_frame(container, left_upper_buttons=["a"], button_font_size=13)
    s_frame = make_s_frame(container, upper_buttons=["a"], button_font_size=13)
    assert frame.buttons["a"].font().pointSize() == 13
    assert s_frame.buttons["a"].font().pointSize() == 13


# ── Relabelling ───────────────────────────────────────────────────────────

def test_set_button_text_keeps_the_key(container):
    frame = make_s_frame(container, upper_buttons=[ButtonInfo("toggle", text="LIST VIEW")])
    frame.set_button_text("toggle", "CARD VIEW")
    assert frame.buttons["toggle"].text() == "CARD VIEW"
    assert frame.button_text("toggle") == "CARD VIEW"
    assert list(frame.buttons) == ["toggle"]


def test_set_button_text_regrows_a_button_that_gains_a_line(container):
    frame = make_frame(container, left_upper_buttons=["a", "b"])
    single = frame.buttons["a"].geometry().height()
    below = frame.buttons["b"].geometry().top()

    frame.set_button_text("a", "TWO\nLINES")

    assert frame.buttons["a"].geometry().height() == 2 * single
    assert frame.buttons["b"].geometry().top() == below + single


def test_set_button_text_reflows_the_rest_of_the_column(container):
    frame = make_s_frame(container, upper_buttons=["a", "b"])
    single = frame.buttons["a"].geometry().height()
    original_b = frame.buttons["b"].geometry().top()

    frame.set_button_text("a", "TWO\nLINES")
    assert frame.buttons["b"].geometry().top() == original_b + single

    frame.set_button_text("a", "ONE LINE")
    assert frame.buttons["a"].geometry().height() == single
    assert frame.buttons["b"].geometry().top() == original_b


def test_set_button_text_leaves_a_fixed_height_button_alone(container):
    frame = make_frame(container, left_upper_buttons=[ButtonInfo("a", height=52)])
    frame.set_button_text("a", "TWO\nLINES")
    assert frame.buttons["a"].geometry().height() == 52


def test_set_button_text_rejects_an_unknown_name(container):
    frame = make_frame(container, left_upper_buttons=["a"])
    with pytest.raises(KeyError):
        frame.set_button_text("nope", "TEXT")


# ── Colour on activation ──────────────────────────────────────────────────

def test_s_frame_keeps_an_explicit_colour_when_the_button_becomes_active(container):
    frame = make_s_frame(
        container,
        upper_buttons=["plain", ButtonInfo("coloured", colour=Colors.rot)],
        color_active=Colors.leuchtblau,
    )
    frame.upper_frame_click("coloured")
    assert frame.upper_active_page == "coloured"
    assert Colors.rot in frame.buttons["coloured"].styleSheet()


def test_s_frame_highlights_a_plain_button_when_it_becomes_active(container):
    frame = make_s_frame(
        container,
        upper_buttons=["first", "second"],
        color_active=Colors.leuchtblau,
    )
    frame.upper_frame_click("second")
    assert Colors.leuchtblau in frame.buttons["second"].styleSheet()


def test_an_explicitly_coloured_first_button_keeps_its_colour(container):
    frame = make_s_frame(
        container,
        lower_buttons=[ButtonInfo("coloured", colour=Colors.rot), "plain"],
        color_active=Colors.leuchtblau,
    )
    assert frame.lower_active_page == "coloured"
    assert Colors.rot in frame.buttons["coloured"].styleSheet()


# ── Sound ─────────────────────────────────────────────────────────────────

def test_injected_play_sound_is_called_on_a_page_switch(container):
    calls = []
    frame = make_s_frame(
        container,
        upper_buttons=["a", "b"],
        lower_buttons=["c", "d"],
        play_sound=lambda: calls.append(1),
    )
    frame.upper_frame_click("b")
    frame.lower_frame_click("d")
    assert len(calls) == 2


def test_frame_uses_an_injected_play_sound(container):
    calls = []
    frame = make_frame(
        container, left_upper_buttons=["a", "b"], play_sound=lambda: calls.append(1),
    )
    frame.frame_click("b")
    assert calls == [1]


def test_a_container_parent_without_sound_is_silent_not_broken(container):
    frame = make_s_frame(container, upper_buttons=["a", "b"])
    frame.upper_frame_click("b")
    assert frame.upper_active_page == "b"


def test_a_parent_that_can_play_sound_is_used_when_none_is_injected(qapp):
    calls = []

    class Noisy(QtWidgets.QWidget):
        def play_sound(self):
            calls.append(1)

    parent = Noisy()
    frame = make_frame(parent, left_upper_buttons=["a", "b"])
    frame.frame_click("b")
    assert calls == [1]


def test_an_injected_handler_beats_the_parents(qapp):
    parent_calls, injected_calls = [], []

    class Noisy(QtWidgets.QWidget):
        def play_sound(self):
            parent_calls.append(1)

    frame = make_frame(
        Noisy(), left_upper_buttons=["a", "b"], play_sound=lambda: injected_calls.append(1),
    )
    frame.frame_click("b")
    assert parent_calls == []
    assert injected_calls == [1]


# ── Page switching still works ────────────────────────────────────────────

def test_pages_switch_independently_in_each_half(container):
    frame = make_s_frame(container, upper_buttons=["a", "b"], lower_buttons=["c", "d"])
    upper_widget = QtWidgets.QLabel(container)
    frame.upper_pages["b"]["label"] = upper_widget
    upper_widget.hide()

    frame.upper_frame_click("b")

    assert frame.upper_active_page == "b"
    assert frame.lower_active_page == "c"
    assert upper_widget.isVisibleTo(container)
