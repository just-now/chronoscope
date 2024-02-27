# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.db as db
import matplotlib.pyplot as pt          # type: ignore
import matplotlib.ticker as ticker      # type: ignore
from yaml import safe_load
import chronoscope.utils as utils


class queue:
    def __init__(self, fig="queue.svg", figsize=(12, 4), unit_of_time="ms"):
        conv = {"ms": 1e6, "us": 1e3}
        self.fig = fig
        self.conv = conv[unit_of_time] if unit_of_time in conv else 1
        self.figsize = figsize
        self.unit_of_time = unit_of_time

    def q_one(self, ev_begin: str, ev_end: str, tk_type: str):
        queues = [s for s in db.queues(ev_begin, ev_end, tk_type)]
        times = [x[0] for x in queues]
        times.insert(0, times[0])
        in_flight = [0]
        in_flight_c = 0
        for x in queues:
            in_flight_c += (x[1] - x[2])
            in_flight.append(in_flight_c)

        pt.title(f"{tk_type}: {ev_begin} — {ev_end}")
        pt.xlabel(f"time({self.unit_of_time})")
        pt.ylabel("in-flight")
        pt.tight_layout()
        pt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(
            lambda value, pos: utils.str_ns(value, compact=True)))
        # pt.plot(times, in_flight, 'r--', linewidth=1)
        pt.step(times, in_flight, 'r--', linewidth=1)

    def queue(self, yspans: str):
        spans: list[dict[str, str]] = safe_load(yspans)
        spans_nr = len(spans)
        pt.figure(figsize=self.figsize)
        for i, s in enumerate(spans):
            type = s["type"]
            span = s["span"]
            pt.subplot(spans_nr, 1, i + 1)
            self.q_one(span[0], span[1], type)
        pt.savefig(fname=self.fig)
