#!/usr/bin/env python

import base64
import socket
import sys
import threading

import firehose.common as common


def _get_myself(fhc):
    print "Select an identity to send as:"
    chums = fhc.get_identities()
    for n, chum in enumerate(chums):
        print "%02d> %s (%s)" % (n, chum.name, chum.keyid)
    inp = raw_input("Enter ID number> ")
    return chums[int(inp)]


def _get_chum(fhc):
    print "Select somebody to send to:"
    chums = fhc.get_chums()
    for n, chum in enumerate(chums):
        print "%02d> %s (%s)" % (n, chum.name, chum.keyid)
    inp = raw_input("Enter ID number> ")
    return chums[int(inp)]


def main_send(gpg, s, myself, chum):
    while True:
        data = raw_input("Send to %s> " % chum.name)
        cmd, _, args = data.partition(" ")
        if cmd == "/me":
            data = "ACT " + args
        elif cmd in ["PING", "PONG"]:
            pass
        else:
            data = "MSG " + data
        data = gpg.encrypt(data, chum.keyid, sign=myself.keyid, passphrase="firehose", always_trust=True)
        s.sendall(base64.b64encode(str(data.data)))


def main_recv(gpg, s):
    while True:
        data = s.recv(4096)
        if not data:
            break
        try:
            data = gpg.decrypt(base64.b64decode(data), passphrase="firehose")
            if data:
                target = data.username or "Unknown"
                print "%s: %s" % (target, data)
        except Exception as e:
            print "Error decoding: %r (%r)" % (data, e)


def main(args=sys.argv):
    fhc = common.FHC()

    try:
        my_key = _get_myself(fhc)
        my_chum_key = _get_chum(fhc)

        s = fhc.sock
        recv = threading.Thread(target=main_recv, args=(fhc.gpg, s))
        recv.daemon = True
        recv.start()
        main_send(fhc.gpg, s, my_key, my_chum_key)
    except (EOFError, KeyboardInterrupt):
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))

