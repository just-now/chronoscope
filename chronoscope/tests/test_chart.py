import sys

import pytest

from chronoscope import chart, parse_args


@pytest.mark.parametrize(("total", "size", "expected"), [
    (4, 5, [0]),
    (10, 4, [0, 2, 4, 6]),
    (11, 4, [0, 2, 4, 6, 7]),
    (12000, 5000, [0, 2500, 5000, 7000]),
])
def test_page_starts(total, size, expected):
    assert chart._page_starts(total, size) == expected


def test_window_size_argument(monkeypatch):
    monkeypatch.setattr(
        sys, "argv", ["chronoscope", "chart", "--window-size", "5000"])
    assert parse_args().window_size == 5000
