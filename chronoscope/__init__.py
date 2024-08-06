# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

from chronoscope import db
from chronoscope import parser
import chronoscope.vcd as vcd
import chronoscope.hist as hist
import chronoscope.tree as tree
import chronoscope.chart as chart
import chronoscope.queue as queue
import chronoscope.drawer as drawer
import argparse as arg
import errno
import sys

__version__ = '0.0.3'
__author__ = 'Anatoliy Bilenko <anatoliy.bilenko@gmail.com>'
__license__ = 'LGPLv3'

db_options: dict[str, int | str] = {
    "cache_size": -128 << 20,
    "synchronous": "off",
    "journal_mode": "off",
}

def parse_args():
    parser = arg.ArgumentParser(prog=sys.argv[0],
                                formatter_class=arg.RawTextHelpFormatter,
                                description="""
    chronoscope: Plots drill-down chart based on user's traces

    Examples:
    chronoscope hist -S \
    "[{type: conn, span:[started,stopped]}, {type: gw, span:[inited,closed]}]"
    """)
    parser.add_argument("-d", "--db", type=str, default="chronoscope.db",
                        help="chronoscope database")
    parser.add_argument("-c", "--conf", type=str, default="chronoscope.yaml",
                        help="configuration, defines how to parse out users'\n"
                        "ticks, attrs and relations from the traces")
    parser.add_argument("-t", "--trace", type=str, help="User's traces")
    parser.add_argument("-D", "--depth", type=int, default=50,
                        help="limits output to given level of ticks")
    parser.add_argument("command", type=str,
                        choices=["create", "chart", "tree",
                                 "hist", "queue", "vcd"],
                        help="create: build chronoscope database\n"
                        "plot: plots drill-down chart for the given tick")
    parser.add_argument("-f", "--fig_size", nargs=2, type=int, default=[16, 4])
    parser.add_argument("-k", "--tick_id", type=int,
                        help="tick identifier to plot")
    parser.add_argument("-S", "--spans", type=str, default="[]",
                        help="histogram spans")
    parser.add_argument("-v", "--verbose", action='store_true',
                        help="print more information")
    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        match args.command:
            case "create":
                db.open(args.db, db_options, create=True, verbose=args.verbose)
                db.load(parser.parser(args.conf, args.verbose), args.trace)
                db.mkidx()
                db.close()
            case "chart":
                db.open(args.db, db_options, verbose=args.verbose)
                chart.plot(args.tick_id, args.fig_size, args.depth)
            case "tree":
                db.open(args.db, db_options, verbose=args.verbose)
                tree.plot(args.tick_id, args.depth)
            case "hist":
                db.open(args.db, db_options, verbose=args.verbose)
                hist.hist().draw(args.spans)
            case "queue":
                db.open(args.db, db_options, verbose=args.verbose)
                queue.queue().draw(args.spans, drawer.orientation.VERTICAL)
            case "vcd":
                db.open(args.db, db_options, verbose=args.verbose)
                vcd.plot(args.tick_id, args.depth)
    except KeyboardInterrupt:
        return errno.EINTR
    except FileExistsError as e:
        print(e, file=sys.stderr)
        return errno.EEXIST
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return errno.EACCES

    return 0
