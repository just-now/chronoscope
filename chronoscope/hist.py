# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.db as db
import scipy.stats as ss                # type: ignore
import matplotlib.pyplot as pt          # type: ignore
from statistics import stdev
import chronoscope.drawer as drawer


class hist(drawer.drawer):
    def __init__(self, fig="hist.svg", figsize=(12, 4), unit_of_time="ms"):
        super().__init__(fig, figsize, unit_of_time)

    def one(self, ev_begin: str, ev_end: str, tk_type: str):
        spans = [s[0] / self.conv for s in db.spans(ev_begin, ev_end, tk_type)]
        tot = len(spans)
        smax = round(max(spans), 2)
        smin = round(min(spans), 2)
        savg = round(sum(spans) / tot, 2)
        stde = round(stdev(spans), 2)
        # rlim = [f for f in spans if options is None or f < options]
        rlim = [f for f in spans]
        rlim_tot = len(rlim)
        ratio_p = round(rlim_tot / tot, 2)

        s1 = fr"$i = [{smin}, {smax}], \mu={savg},\ \sigma={stde}$"
        s2 = fr"$n = {tot}, nr = {rlim_tot}, nr/n = {ratio_p}$"
        pt.title(f"{tk_type}: {ev_begin} — {ev_end}\n{s1}\n{s2}")
        pt.xlabel(f"time({self.unit_of_time})")
        pt.ylabel("frequency")
        n, bins, patches = pt.hist(rlim, bins=50, facecolor='green', alpha=0.7)
        y = ss.norm.pdf(bins, savg, stde)
        pt.tight_layout()
        pt.plot(bins, y, 'r--', linewidth=1)
