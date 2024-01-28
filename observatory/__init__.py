# -*- coding: utf-8 -*-
#
# This file is part of Observatory.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

from observatory import db
from observatory import parser
from observatory.chart import plot
import argparse
import sys

__version__ = '0.0.1'
__author__ = 'Anatoliy Bilenko <anatoliy.bilenko@gmail.com>'
__license__ = 'LGPLv3'

db_options: dict[str, int | str] = {
    "cache_size": -128 << 20,
    "synchronous": "off",
    "journal_mode": "off",
}

def parse_args():
    parser = argparse.ArgumentParser(prog=sys.argv[0], description="""
    observatory: Plots drill-down chart based on user's traces""")
    parser.add_argument("-d", "--db", type=str, default="observatory.db",
                        help="observatory database")
    parser.add_argument("-c", "--conf", type=str, default="observatory.yaml",
                        help="configuration, defines how to parse out users'\n"
                        "ticks, attrs and relations from the traces")
    parser.add_argument("-t", "--trace", type=str, help="User's traces")
    parser.add_argument("-D", "--depth", type=int, default=50,
                        help="limits output to given level of ticks")
    parser.add_argument("command", type=str, choices=["create", "plot"],
                        help="create: build observatory database\n"
                        "plot: plots drill-down chart for the given tick")
    parser.add_argument("-k", "--tick_id", type=int,
                        help="tick identifier to plot")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "create":
        db.open(args.db, db_options, create=True)
        db.load(parser.parser(args.conf), args.trace)
        db.mkidx()
        db.close()

    if args.command == "plot":
        db.open(args.db, db_options)
        plot(args.tick_id)

    return 0
