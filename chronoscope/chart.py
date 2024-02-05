# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import chronoscope.db as db
import chronoscope.utils as utils
import matplotlib.cm as cm              # type: ignore
import matplotlib.pyplot as pt          # type: ignore
import matplotlib.ticker as ticker      # type: ignore
from dataclasses import dataclass
import sys


Y_LINE_SPACING = 2
X_TICKS_MAX = 5

def plot_timeline(timeline, y_pos: int):
    y_pos_scaled = -Y_LINE_SPACING * y_pos
    colors = cm.get_cmap("tab10").colors  # type: ignore[attr-defined]

    for current, current_tick in enumerate(timeline[:-1]):
        next_tick = timeline[current + 1]
        start_time, end_time = current_tick["time"], next_tick["time"]
        event_label = current_tick["event"]

        pt.hlines(y_pos_scaled, start_time, end_time, lw=4,
                  colors=colors[current % len(colors)])
        pt.text(start_time, y_pos_scaled, event_label, rotation=90)

    pt.text(timeline[-1]["time"], y_pos_scaled,
            timeline[-1]["event"], rotation=90)

@dataclass
class timeline_visitor:
    y_labels: list
    y_pos: int
    x_min: int
    x_max: int

    def __call__(self, timeline: list[dict], origin: int, parent: None | int):
        plot_timeline(timeline, self.y_pos)
        self.y_pos += 1
        duration = round((timeline[-1]["time"] - timeline[0]["time"]) / 1e6, 3)
        type, id = timeline[0]["type"], timeline[0]["id"]
        self.y_labels.append(f"{type}{utils.unpack(id)} [{duration}ms]")

        times = [tick["time"] for tick in timeline]
        self.x_min = min(self.x_min, min(times))
        self.x_max = max(self.x_max, max(times))

class chart_annotation:
    def __init__(self, fig):
        self.cur_mark = ord('A')
        self.cur = []
        self.ann = []
        self.ann_mode = False
        fig.canvas.mpl_connect("key_press_event", self.on_key)
        fig.canvas.mpl_connect("button_press_event", self.on_click)

    def on_key(self, event):
        if event.key == "escape":
            sys.exit(1)
        elif event.key == "e":
            self.ann_mode = not self.ann_mode
        elif event.key == "d":
            if self.ann:
                self.cur_mark -= 1
                self.cur.pop()
                self.ann.pop().remove()
                self.ann.pop().remove()
            event.canvas.draw()

    def on_click(self, event):
        if not self.ann_mode:
            return

        x, ax = event.xdata, event.inaxes
        # TODO: Don't ask me what's going on with cursors... I don't know!
        self.cur.append(x)
        cursor = chr(self.cur_mark)
        if self.cur_mark % 2 == 0:
            cursor = chr(self.cur_mark - 1) + cursor + ": "
            cursor += utils.str_ns_diff(int(abs(self.cur[-1] - self.cur[-2])))
        self.cur_mark += 1

        self.ann.append(ax.axvline(x=x, color="lightgray"))
        self.ann.append(ax.annotate(cursor, xycoords=("data", "axes fraction"),
                                    xy=(x, 0)))
        self.ann_mode = not self.ann_mode
        event.canvas.draw()

def plot(origin: int, figsize=(16, 4), depth_max=50):
    fig = pt.figure(figsize=figsize)
    pt.style.use("bmh")
    pt.rcParams["font.size"] = 8
    pt.subplots_adjust(top=0.75)

    v = timeline_visitor([], 0, utils.MAX_INT, utils.MIN_INT)
    db.iterate(origin, None, db.tick, v, 0, depth_max)

    end = -Y_LINE_SPACING * v.y_pos
    y_range = [float(x) for x in range(0, end, -Y_LINE_SPACING)]
    x_range = range(v.x_min, v.x_max, round((v.x_max - v.x_min) / X_TICKS_MAX))

    # (1)
    # x_labels = [utils.str_ns(x, compact=True) for x in x_range]
    # pt.xticks(x_range, x_labels)
    # (2) This might be slow, consider to uncomment (1) in such cases.
    pt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda value, pos: utils.str_ns(value, compact=True)))

    pt.yticks(y_range, v.y_labels)
    pt.xlabel("Time")
    pt.autoscale(enable=True, axis="x", tight=True)
    pt.margins(0.1)
    _ = chart_annotation(fig)

    pt.grid(True)
    title = f"Request {utils.unpack(origin)}\n"
    title += f"[{utils.str_ns(x_range[0])}...{utils.str_ns(x_range[-1])}]"
    pt.suptitle(title)
    pt.show()
