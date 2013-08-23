#!/usr/bin/env python

import base64
import sys

import firehose.common as common


def _select(chums, prompt):
    print prompt
    for n, chum in enumerate(chums):
        print "%02d> %s (%s)" % (n, chum.name, chum.keyid)
    inp = raw_input("Enter ID number> ")
    return chums[int(inp)]


def main_send(chum):
    while True:
        data = raw_input("Send to %s> " % chum.name)
        cmd, _, args = data.partition(" ")
        if cmd == "/me":
            data = "ACT " + args
        elif cmd in ["PING", "PONG"]:
            pass
        else:
            data = "MSG " + data
        chum.send(data)


def main_recv(chum, data):
    print "%s: %s" % (chum.name, data.data)


def main(args=sys.argv):
    fhc = common.FHC()

    try:
        my_self = _select(fhc.get_identities(), "Select an identity to send as:")
        my_chum = _select(fhc.get_chums(), "Select somebody to send to:")

        fhc.set_identity(my_self)
        fhc.start(main_recv)
        main_send(my_chum)
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))

