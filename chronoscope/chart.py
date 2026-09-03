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

    def collect_arrows(self, event_range=None):
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
        params = ()
        if event_range is not None:
            first_time, first_id, last_time, last_id = event_range
            sql += """
            AND (source.time, source.id) >= (?, ?)
            AND (source.time, source.id) <= (?, ?)
            AND (target.time, target.id) >= (?, ?)
            AND (target.time, target.id) <= (?, ?)
            """
            params = (first_time, first_id, last_time, last_id) * 2
        rows = db.db.execute_sql(sql, params).fetchall()
        for from_sm, from_time, to_sm, to_time in rows:
            if from_sm in self.sm_to_y and to_sm in self.sm_to_y:
                self.arrows.append((
                    from_time, -Y_LINE_SPACING * self.sm_to_y[from_sm],
                    to_time,   -Y_LINE_SPACING * self.sm_to_y[to_sm],
                ))

def plot_arrows(arrows: list):
    artists = []
    for from_time, from_y, to_time, to_y in arrows:
        artists.append(pt.annotate(
            "", xy=(to_time, to_y), xytext=(from_time, from_y),
            arrowprops=dict(arrowstyle="-|>", color="navy",
                            lw=0.6, alpha=0.7,
                            shrinkA=2, shrinkB=2),
            zorder=10))
    return artists


class event_relation_toggle:
    def __init__(self, fig):
        self.visible = True
        self.artists = []
        fig.canvas.mpl_connect("key_press_event", self.on_key)

    def replace(self, artists):
        self.artists = artists
        for artist in artists:
            artist.set_visible(self.visible)

    def on_key(self, event):
        if event.key != "a":
            return
        self.visible = not self.visible
        for artist in self.artists:
            artist.set_visible(self.visible)
        event.canvas.draw_idle()

class chart_annotation:
    def __init__(self, fig):
        self.reset()
        fig.canvas.mpl_connect("key_press_event", self.on_key)
        fig.canvas.mpl_connect("button_press_event", self.on_click)

    def reset(self):
        self.cur_mark = ord('A')
        self.cur = []
        self.ann = []
        self.ann_mode = False

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

def _draw(fig, origin: int, figsize, depth_max: int, reverse: bool,
          event_range=None, page_label=None):
    fig.clear()
    pt.figure(fig.number)
    pt.style.use("bmh")
    pt.rcParams["font.size"] = 8
    pt.subplots_adjust(top=0.75)

    v = timeline_visitor([], 0, utils.MAX_INT, utils.MIN_INT)
    db.iterate(origin, None, v, 0, depth_max, reverse, event_range)
    v.collect_arrows(event_range)

    end = -Y_LINE_SPACING * v.y_pos
    y_range = [float(x) for x in range(0, end, -Y_LINE_SPACING)]
    tick_step = max(1, round((v.x_max - v.x_min) / X_TICKS_MAX))
    x_range = range(v.x_min, v.x_max + 1, tick_step)

    # (1)
    # x_labels = [utils.str_ns(x, compact=True) for x in x_range]
    # pt.xticks(x_range, x_labels)
    # (2) This might be slow, consider to uncomment (1) in such cases.
    pt.gca().xaxis.set_major_formatter(ticker.FuncFormatter(
        lambda value, pos: utils.str_ns(value, compact=True)))

    arrow_artists = plot_arrows(v.arrows)
    pt.yticks(y_range, v.y_labels)
    pt.xlabel("Time")
    pt.autoscale(enable=True, axis="x", tight=True)
    pt.margins(0.1)
    # Keep the callback owner alive after non-blocking show() returns in
    # notebook backends such as ipympl. Matplotlib stores weak references to
    # bound-method callbacks.
    pt.grid(True)
    title = f"Request {utils.format_event_id(origin)}\n"
    title += f"[{utils.str_ns(x_range[0])}...{utils.str_ns(x_range[-1])}]"
    if page_label is not None:
        title += f"\nEvents {page_label}"
    pt.suptitle(title)
    return arrow_artists


def _page_starts(total: int, size: int) -> list[int]:
    last = max(0, total - size)
    step = max(1, size // 2)
    starts = list(range(0, last + 1, step))
    if starts[-1] != last:
        starts.append(last)
    return starts


class chart_pager:
    def __init__(self, fig, origin: int, figsize, depth_max: int,
                 reverse: bool, window_size: int):
        if window_size <= 0:
            raise ValueError("window size must be greater than zero")
        self.fig = fig
        self.origin = origin
        self.figsize = figsize
        self.depth_max = depth_max
        self.reverse = reverse
        self.window_size = window_size
        self.sm_ids = db.state_machine_ids(origin, depth_max, reverse)
        self.total, _ = db.event_page(self.sm_ids, 0, window_size)
        self.starts = _page_starts(self.total, window_size)
        self.page = 0
        self.annotation = chart_annotation(fig)
        self.relation_toggle = event_relation_toggle(fig)
        fig.canvas.mpl_connect("key_press_event", self.on_key)

    def draw(self):
        start = self.starts[self.page]
        _, rows = db.event_page(self.sm_ids, start, self.window_size)
        event_range = None
        if rows:
            event_range = (*rows[0], *rows[-1])
        self.annotation.reset()
        page_label = f"[{start}:{start + len(rows)}) of {self.total}"
        artists = _draw(self.fig, self.origin, self.figsize, self.depth_max,
                        self.reverse, event_range, page_label)
        self.relation_toggle.replace(artists)
        self.fig.canvas.draw_idle()

    def on_key(self, event):
        old_page = self.page
        if event.key == "[":
            self.page = max(0, self.page - 1)
        elif event.key == "]":
            self.page = min(len(self.starts) - 1, self.page + 1)
        elif event.key == "<":
            self.page = 0
        elif event.key == ">":
            self.page = len(self.starts) - 1
        if self.page != old_page:
            self.draw()


def plot(origin: int, figsize=(16, 4), depth_max=50, reverse=False,
         window_size=None):
    fig = pt.figure(figsize=figsize)
    if window_size is None:
        artists = _draw(fig, origin, figsize, depth_max, reverse)
        setattr(fig, "_chronoscope_annotation", chart_annotation(fig))
        relation_toggle = event_relation_toggle(fig)
        relation_toggle.replace(artists)
        setattr(fig, "_chronoscope_relation_toggle", relation_toggle)
    else:
        pager = chart_pager(fig, origin, figsize, depth_max, reverse,
                            window_size)
        pager.draw()
        setattr(fig, "_chronoscope_pager", pager)
    pt.show()
