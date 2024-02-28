# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import matplotlib.pyplot as pt          # type: ignore
from yaml import safe_load
from enum import Enum
from abc import abstractmethod

class orientation(Enum):
    VERTICAL = 1
    HORIZONTAL = 2

class drawer:
    @abstractmethod
    def one(self, ev_begin: str, ev_end: str, tk_type: str): pass  # noqa

    def __init__(self, fig: str, figsize: tuple, unit_of_time: str):
        conv = {"ms": 1e6, "us": 1e3}
        self.fig = fig
        self.conv = conv[unit_of_time] if unit_of_time in conv else 1
        self.figsize = figsize
        self.unit_of_time = unit_of_time

    def draw(self, yspans: str, orient=orientation.HORIZONTAL):
        spans: list[dict[str, str]] = safe_load(yspans)
        spans_nr = len(spans)
        pt.figure(figsize=self.figsize)
        for i, s in enumerate(spans):
            match orient:
                case orientation.HORIZONTAL:
                    pt.subplot(1, spans_nr, i + 1)
                case orientation.VERTICAL:
                    pt.subplot(spans_nr, 1, i + 1)

            type = s["type"]
            span = s["span"]
            self.one(span[0], span[1], type)
        pt.savefig(fname=self.fig)
