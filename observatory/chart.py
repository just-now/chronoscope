# -*- coding: utf-8 -*-
#
# This file is part of Observatory.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

import observatory.db as db
import observatory.utils as utils
import matplotlib.cm as cm
import matplotlib.pyplot as pt
from typing import Callable


iter_depth_max = 50
y_line_spacing = 2
x_ticks_max = 5

def iterate(origin: int, depth: int, depth_max: int, visit: Callable):
    if depth_max < depth:
        return

    # pull timeline
    if timeline := db.tick.select().where((db.tick.id == origin)):
        visit([tick for tick in timeline.dicts()])

    # pull children timelines
    children = db.relation.select().where((db.relation.orig == origin))
    for child in children.dicts():
        print(f"@[{depth}] {hex(child['orig'])} ... {hex(child['dest'])} ...")
        iterate(child["dest"], depth + 1, depth_max, visit)

def plot_timeline(timeline, y_pos: int):
    y_pos_scaled = -y_line_spacing * y_pos
    colors = cm.get_cmap("tab10").colors

    for current, current_tick in enumerate(timeline[:-1]):
        next_tick = timeline[current + 1]
        start_time, end_time = current_tick["time"], next_tick["time"]
        event_label = current_tick["event"]

        pt.hlines(y_pos_scaled, start_time, end_time, lw=4,
                  colors=colors[current % len(colors)])
        pt.text(start_time, y_pos_scaled, event_label, rotation=90)

    first_tick, last_tick = timeline[0], timeline[-1]
    start_time, end_time = first_tick["time"], last_tick["time"]
    last_event_label = last_tick["event"]
    pt.text(end_time, y_pos_scaled, last_event_label, rotation=90)

    duration = end_time - start_time
    duration_label = f"{first_tick['type']}: {round(duration / 1e6, 3)}ms"
    duration_label_x_pos = (end_time + start_time) / 2
    pt.text(duration_label_x_pos, y_pos_scaled + 0.05, duration_label)

def plot(origin: int):
    y_pos = 0
    y_labels = []
    x_min = utils.max_int
    x_max = utils.min_int

    def visit(timeline: list[dict]):
        nonlocal y_labels, y_pos, x_min, x_max
        plot_timeline(timeline, y_pos)
        type = timeline[0]["type"]
        id = timeline[0]["id"]
        y_pos += 1
        y_labels.append(f"{type}\n{hex(id)}")
        x_min = min(x_min, min([t["time"] for t in timeline]))
        x_max = max(x_max, max([t["time"] for t in timeline]))

    pt.style.use("bmh")
    pt.rcParams["font.size"] = 8
    pt.subplots_adjust(top=0.75)

    iterate(origin, 0, iter_depth_max, visit)

    end = -y_line_spacing * y_pos
    y_range = [float(x) for x in range(0, end, -y_line_spacing)]
    pt.yticks(y_range, y_labels)

    x_range = range(x_min, x_max, round((x_max - x_min) / x_ticks_max))
    x_labels = [utils.strns(x, compact=(x != x_range[0])) for x in x_range]
    pt.xticks(x_range, x_labels)
    pt.xlabel('Time')
    pt.autoscale(enable=True, axis='x', tight=True)

    pt.grid(True)
    pt.suptitle(f"Request {hex(origin)}")
    pt.show()
