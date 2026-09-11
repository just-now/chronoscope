#!/usr/bin/env -S gawk -M -f

# Translates the old text-based log format into the new per-line JSON one,
# enabling old logs to be used with the new chronoscope parser.
#
# Discrepancies between the legacy text format and the schema:
#
# 1. `event_relation` lines carry a single sm_id, while the schema requires
#    from_sm_id and to_sm_id. That one id is written to BOTH fields; the
#    source event's actual state machine is not resolved.
#
# 2. `event_relation` lines carry no `relation` value. A constant,
#    PLACEHOLDER_RELATION_NAME, is emitted instead.
#
# 3. `event_relation` lines carry no from_time or to_time. Those DB-only
#    fields are derived by the JSON parser from the top-level timestamp.
#
# 4. `raft` lines declare no state-machine creation. The first event seen
#    for an sm_id additionally emits a `state_machine` record named "raft".
#
# 5. `state_machine` lines carry a `state=`/`eid=` pair declaring a state
#    transition on the machine. Such a line emits its creation
#    `state_machine` record (once per sm_id) followed by a transition
#    `event`; a bare line emits only the creation record.
#
# Ids are emitted as decimal integers per the schema ("identifier": integer);
# gawk -M (arbitrary precision) is REQUIRED so 64-bit hex values convert
# without precision loss. Run via the shebang or `gawk -M -f convert-trace.awk`.

BEGIN {
    errors = 0
}

/\|$/ {
    split("", fields)      # clear per-record state (arrays are global)
    split("", extra_fields)

    fields["timestamp"] = $2

    type = $3
    switch (type) {
        case "raft":
            # Input:  raft[1]: 2026-09-03T10:44:20.281531038 raft sm_id: 0x1000000000000001 eid=0x1000000000000002 restart |

            extra_fields["type"] = "event"

            sm_id = parse_id($5)
            extra_fields["state_machine_id"] = sm_id

            key_value($6, eid_kv)
            extra_fields["id"] = parse_id(eid_kv["value"])

            extra_fields["name"] = $7

            # The legacy format has no creation record for raft state
            # machines; derive one from the first event seen for the sm_id.
            if (!(sm_id in seen_sms)) {
                seen_sms[sm_id] = 1
                split("", sm_fields)
                sm_fields["timestamp"] = fields["timestamp"]
                split("", sm_extra)
                sm_extra["type"] = "state_machine"
                sm_extra["id"] = sm_id
                sm_extra["name"] = "raft"
                print_record(sm_fields, sm_extra)
            }

            break
        case "event_attribute":
            # Input:  raft[1]: 2026-09-03T10:44:20.281633910 event_attribute eid=0x1000000000000002 raft:role=Follower |

            extra_fields["type"] = "event_attribute"

            key_value($4, eid_kv)
            extra_fields["event_id"] = parse_id(eid_kv["value"])

            key_value($5, attr_kv)
            extra_fields["key"] = attr_kv["key"]
            extra_fields["value"] = attr_kv["value"]

            break
        case "event_relation":
            # Input:  raft[1]: 2026-09-03T10:44:20.319097740 event_relation sm_id: 0x100000000000000b eid=0x1000000000000015 peid=0x1000000000000011 |

            extra_fields["type"] = "event_relation"

            key_value($6, eid_kv)
            extra_fields["to_event_id"] = parse_id(eid_kv["value"])

            key_value($7, peid_kv)
            extra_fields["from_event_id"] = parse_id(peid_kv["value"])

            # Placeholder due to missing data in old format.
            extra_fields["relation"] = "PLACEHOLDER_RELATION_NAME"

            # This is a placeholder, these fields will be ignored. It's
            # sufficient to have the two event ids, and the name of the
            # relation.
            extra_fields["from_sm_id"] = parse_id($5)
            extra_fields["to_sm_id"] = parse_id($5)

            break
        case "state_machine":
            # Input (creation):  sm[70205]: <ts> state_machine sm_id=0x…003 name=FirstRecordState |
            # Input (transition): sm[70205]: <ts> state_machine sm_id=0x…003 name=FirstRecordState state=NotALeader eid=0x…004 |
            #
            # A line carrying `state=` and `eid=` declares a state
            # transition and becomes an `event`; a bare line declares the
            # creation of a new state machine and becomes a `state_machine`
            # record.
            #
            # This dual-handling originates from ambiguity in the legacy
            # input gathered in practice whereby `state_machine` was used
            # to represent `event` traces, and the Raft state machine was
            # never explicitly declared. It is a hack.
            key_value($4, sm_id_kv)
            sm_id = parse_id(sm_id_kv["value"])
            key_value($5, name_kv)
            if (!(sm_id in seen_sms)) {
                seen_sms[sm_id] = 1
                split("", sm_fields)
                sm_fields["timestamp"] = fields["timestamp"]
                split("", sm_extra)
                sm_extra["type"] = "state_machine"
                sm_extra["id"] = sm_id
                sm_extra["name"] = name_kv["value"]
                print_record(sm_fields, sm_extra)
            }

            if ($6 ~ /^state=/ && $7 ~ /^eid=/) {
                extra_fields["type"] = "event"
                extra_fields["state_machine_id"] = sm_id

                key_value($6, state_kv)
                extra_fields["name"] = state_kv["value"]

                key_value($7, eid_kv)
                extra_fields["id"] = parse_id(eid_kv["value"])
            } else {
                extra_fields["type"] = "state_machine"
                extra_fields["id"] = sm_id
                extra_fields["name"] = name_kv["value"]
            }

            break
        case "state_machine_relation":
            # Input:  sm[1]: 2025-06-07T11:00:14.026305714 state_machine_relation from_sm_id=0x7000000000000001 to_sm_id=0x1000000000000001 relation=top-to-raft |

            extra_fields["type"] = "state_machine_relation"

            key_value($4, from_kv)
            extra_fields["from_sm_id"] = parse_id(from_kv["value"])

            key_value($5, to_kv)
            extra_fields["to_sm_id"] = parse_id(to_kv["value"])

            key_value($6, rel_kv)
            extra_fields["relation"] = rel_kv["value"]

            break
        default:
            printf "UNKNOWN TYPE: %s\n", type | "cat 1>&2"
            errors++
            next
    }

    print_record(fields, extra_fields)
}

END {
    if (errors > 0) {
        printf "%d error(s) occurred\n", errors | "cat 1>&2"
        exit 1
    }
}

# ---------------
# --- Helpers ---
# ---------------

# Emits one JSONL record.
function print_record(fields, extra_fields) {
    printf "{"
    print_entries(fields)
    printf ",\"extra_fields\":{"
    print_entries(extra_fields)
    printf "}"
    printf "}\n"
}

# Prints `"key": "value", "key2": value2, ...`
function print_entries(entries,    keys, n_entries, add_comma, i, key) {
    # Constant alphabetical key order for better diffing.
    n_entries = asorti(entries, keys)

    add_comma = 0
    for (i = 1; i <= n_entries; i++) {
        key = keys[i]

        if (add_comma) {
            printf ","
        }
        add_comma = 1

        printf "\"%s\":%s", key, fmt(entries[key])
    }
}

# Heuristically reformats string values as JSON ones. Boolean-looking trace
# values are emitted as JSON booleans; the JSON parser normalizes them back to
# lowercase text before database insertion, matching the legacy text parser.
#
# Assumption: input values never contain a double quote, so string values do
# not require quote escaping here.
function fmt(value) {
    if (match(value, /^[0-9]+$/) || match(value, /^(true|false)$/)) {
        return value
    }
    return sprintf("\"%s\"", value)
}

# 64-bit hex id -> exact decimal integer (needs gawk -M); passthrough otherwise.
function parse_id(value) {
    if (match(value, /^0x[0-9a-fA-F]+$/)) {
        return sprintf("%d", strtonum(value))
    }
    return value
}

# Parses given `key=value` string.
function key_value(raw, ret) {
    match(raw, /(.*)=/)
    ret["key"] = substr(raw, RSTART, RLENGTH-1)

    match(raw, /=(.*)/)
    ret["value"] = substr(raw, RSTART+1, RLENGTH-1)
}
