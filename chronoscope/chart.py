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
from dataclasses import dataclass, field
import sys


Y_LINE_SPACING = 2
X_TICKS_MAX = 5

def plot_timeline(timeline, y_pos: int):
    y_pos_scaled = -Y_LINE_SPACING * y_pos

    for current, current_tick in enumerate(timeline[:-1]):
        next_tick = timeline[current + 1]
        start_time, end_time = current_tick["time"], next_tick["time"]
        event_label = current_tick["name"]

        pt.hlines(y_pos_scaled, start_time, end_time, lw=4,
                  colors=cm.tab10(current % 7))  # type: ignore[attr-defined]
        pt.text(start_time, y_pos_scaled, event_label, rotation=90)

    if len(timeline[:]) == 1:
        pt.hlines(y_pos_scaled, timeline[0]["time"], timeline[0]["time"])

    pt.text(timeline[-1]["time"], y_pos_scaled,
            timeline[-1]["name"], rotation=90)

@dataclass
class timeline_visitor:
    y_labels: list
    y_pos: int
    x_min: int
    x_max: int
    # sm_id -> y_pos, for drawing event_relation arrows
    sm_to_y: dict = field(default_factory=dict)
    # (from_time, from_y, to_time, to_y) pairs for thin arrows
    arrows: list = field(default_factory=list)

    def __call__(self, timeline: list[dict], origin: int, parent: None | int):
        if not timeline:
            self.sm_to_y[origin] = self.y_pos
            self.y_pos += 1
            self.y_labels.append(f"?{utils.format_event_id(origin)} [empty]")
            return
        plot_timeline(timeline, self.y_pos)
        self.sm_to_y[origin] = self.y_pos
        duration = round((timeline[-1]["time"] - timeline[0]["time"]) / 1e6, 3)
        sm_type = timeline[0].get("sm_type", "?")
        label = f"{sm_type}{utils.format_event_id(origin)} [{duration}ms]"
        self.y_labels.append(label)

        times = [tick["time"] for tick in timeline]
        self.x_min = min(self.x_min, min(times))
        self.x_max = max(self.x_max, max(times))
        self.y_pos += 1

    def collect_arrows(self):
        """Resolve both arrow endpoints through their referenced events."""
        sql = """
        SELECT source.state_machine_id AS from_sm,
               source.time AS from_time,
               target.state_machine_id AS to_sm,
               target.time AS to_time
        FROM event_relation r
        JOIN event source ON source.id = r.from_event_id
        JOIN event target ON target.id = r.to_event_id
        WHERE r.from_event_id IS NOT NULL
        """
        for from_sm, from_time, to_sm, to_time in db.db.execute_sql(sql).fetchall():
            if from_sm in self.sm_to_y and to_sm in self.sm_to_y:
                self.arrows.append((
                    from_time, -Y_LINE_SPACING * self.sm_to_y[from_sm],
                    to_time,   -Y_LINE_SPACING * self.sm_to_y[to_sm],
                ))

def plot_arrows(arrows: list):
    for from_time, from_y, to_time, to_y in arrows:
        pt.annotate("",
                    xy=(to_time, to_y), xytext=(from_time, from_y),
                    arrowprops=dict(arrowstyle="-|>", color="navy",
                                    lw=0.6, alpha=0.7,
                                    shrinkA=2, shrinkB=2),
                    zorder=10)

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
            cursor += utils.str_us_diff(int(abs(self.cur[-1] - self.cur[-2])))
        self.cur_mark += 1

        self.ann.append(ax.axvline(x=x, color="lightgray"))
        self.ann.append(ax.annotate(cursor, xycoords=("data", "axes fraction"),
                                    xy=(x, 0)))
        self.ann_mode = not self.ann_mode
        event.canvas.draw()

def plot(origin: int, figsize=(16, 4), depth_max=50, reverse=False):
    fig = pt.figure(figsize=figsize)
    pt.style.use("bmh")
    pt.rcParams["font.size"] = 8
    pt.subplots_adjust(top=0.75)

    v = timeline_visitor([], 0, utils.MAX_INT, utils.MIN_INT)
    db.iterate(origin, None, v, 0, depth_max, reverse)
    v.collect_arrows()

    end = -Y_LINE_SPACING * v.y_pos
    y_range = [float(x) for x in range(0, end, -Y_LINE_SPACING)]
    x_range = range(v.x_min, v.x_max, round((v.x_max - v.x_min) / X_TICKS_MAX))

    # (1)
    # x_labels = [utils.str_ns(x, compact=True) for x in x_range]
    # pt.xticks(x_range, x_labels)
    # (2) This might be slow, consider to uncomment (1) in such cases.
    pt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda value, pos: utils.str_ns(value, compact=True)))

    plot_arrows(v.arrows)
    pt.yticks(y_range, v.y_labels)
    pt.xlabel("Time")
    pt.autoscale(enable=True, axis="x", tight=True)
    pt.margins(0.1)
    # Keep the callback owner alive after non-blocking show() returns in
    # notebook backends such as ipympl. Matplotlib stores weak references to
    # bound-method callbacks.
    setattr(fig, "_chronoscope_annotation", chart_annotation(fig))

    pt.grid(True)
    title = f"Request {utils.format_event_id(origin)}\n"
    title += f"[{utils.str_ns(x_range[0])}...{utils.str_ns(x_range[-1])}]"
    pt.suptitle(title)
    pt.show()
