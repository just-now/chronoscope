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
import chronoscope.utils as utils
import chronoscope.drawer as drawer


class queue(drawer.drawer):
    def __init__(self, fig="queue.svg", figsize=(12, 4), unit_of_time="ms"):
        super().__init__(fig, figsize, unit_of_time)

    def one(self, ev_begin: str, ev_end: str, tk_type: str):
        queues = [s for s in db.queues(ev_begin, ev_end, tk_type)]
        times = [x[0] for x in queues]
        in_flight = []
        in_flight_c = 0
        for x in queues:
            in_flight_c += x[1] - x[2]
            in_flight.append(in_flight_c)

        pt.title(f"{tk_type}: {ev_begin} — {ev_end}")
        pt.xlabel(f"time({self.unit_of_time})")
        pt.ylabel("in-flight")
        pt.tight_layout()
        pt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(
            lambda value, pos: utils.str_ns(value, compact=True)))
        pt.plot(times, in_flight, 'r--', linewidth=1)
