# -*- coding: utf-8 -*-
#
# This file is part of Chronoscope.
#
# SPDX-FileCopyrightText: 2024 Anatoliy Bilenko <anatoliy.bilenko@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0-only
#

from datetime import datetime as t
import sys

NS_TIME_LEN = len("2055-11-29T20:57:56.489282133")
FMT_US = "%Y-%m-%dT%H:%M:%S.%f"
FMT_US_COMPACT = ":%S.%f"
MAX_INT = sys.maxsize
MIN_INT = -sys.maxsize - 1
BITS_PER_PID = 16
DB_INT_SIZE = 64
NET_PID_BITS = 4
BOOT_COUNTER_BITS = 12
EVENT_COUNTER_BITS = 48


def pack_unpack_init(p_bits_per_pid: int, p_db_int_size: int):
    global BITS_PER_PID, DB_INT_SIZE
    BITS_PER_PID = p_bits_per_pid
    DB_INT_SIZE = p_db_int_size

def pack(id: int, pid: int) -> int:
    masked_pid = ((1 << BITS_PER_PID) - 1) & pid
    packed_pid = masked_pid << (DB_INT_SIZE - BITS_PER_PID)
    packed_id = ((1 << (DB_INT_SIZE - BITS_PER_PID)) - 1) & id
    return (packed_pid | packed_id)

def unpack(id_pid: int) -> tuple[int, int]:
    pid = id_pid >> (DB_INT_SIZE - BITS_PER_PID)
    id = ((1 << (DB_INT_SIZE - BITS_PER_PID)) - 1) & id_pid
    return pid, id

def unpack_event_id(event_id: int) -> tuple[int, int, int]:
    net_pid = event_id >> (BOOT_COUNTER_BITS + EVENT_COUNTER_BITS)
    boot_mask = (1 << BOOT_COUNTER_BITS) - 1
    boot_counter = (event_id >> EVENT_COUNTER_BITS) & boot_mask
    counter = event_id & ((1 << EVENT_COUNTER_BITS) - 1)
    return net_pid, boot_counter, counter

def format_event_id(event_id: int) -> str:
    net_pid, boot_counter, counter = unpack_event_id(event_id)
    return f"({net_pid} {boot_counter} {counter})"

def ns(time: str) -> int:
    if len(time) != NS_TIME_LEN:
        raise ValueError("Not a nanosecond time format")
    us = int(t.strptime(time[:-3], FMT_US).timestamp() * 1e6)
    return us * 1_000 + int(time[-3:])

def str_ns(unix_time_ns: int, compact=False) -> str:
    dt = t.utcfromtimestamp(unix_time_ns / 1e9)
    if compact:
        return dt.strftime(FMT_US_COMPACT)
    return dt.strftime(FMT_US)


def str_us_diff(unix_time_ns: int) -> str:
    return str(unix_time_ns // 1_000) + "us"
