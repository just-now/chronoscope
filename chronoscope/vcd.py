# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.utils as u
import chronoscope.db as db
import vcd.gtkw
import vcd


class timeline_visitor:
    def __init__(self, gtkw, writer, counters, timetable):
        self.gtkw = gtkw
        self.writer = writer
        self.counters = counters
        self.timetable = timetable

    def __call__(self, timeline: list[dict], origin: int, parent: None | int):
        t0 = timeline[0]
        var = "{}_{}_{}".format(t0["type"], *u.unpack(t0["id"]))

        ctr = self.writer.register_var("c", var, "string")
        self.gtkw.trace(f"c.{var}")

        self.counters[var] = ctr
        self.timetable += [{"var": var, "time": t["time"], "event": t["event"]}
                           for t in timeline]


def plot(origin: int, depth_max=50):
    w = "vcd_{}_{}".format(*u.unpack(origin))
    with open(f"{w}.vcd", "w") as fout, open(f"{w}.gtkw", "w") as wf:
        gtkw = vcd.gtkw.GTKWSave(wf)
        gtkw.dumpfile(f"{w}.vcd")

        with vcd.VCDWriter(fout, timescale="1 ns", date="today") as writer:
            counters: dict = {}
            timetable: list[dict] = []
            v = timeline_visitor(gtkw, writer, counters, timetable)
            db.iterate(origin, None, db.tick, v, 0, depth_max)

            timetable.sort(key=lambda t: t["time"])
            t0 = timetable[0]["time"]
            for t in timetable:
                writer.change(counters[t["var"]], t["time"] - t0, t["event"])
