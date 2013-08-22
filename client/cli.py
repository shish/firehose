#!/usr/bin/env python

import gnupg
import uuid
import base64
import socket
import sys
import argparse
import threading


def _get_my_key(gpg):
    print "Select an identity to send as:"
    keys = gpg.list_keys(True)
    for n, key in enumerate(keys):
        print "%02d> %s (%s)" % (n, key["uids"][0], key["keyid"])
    inp = raw_input("Enter ID number (or blank to be anonymous)> ")
    try:
        return keys[int(inp)]
    except Exception as e:
        return {"keyid": None, "uids": ["Anonymous"]}


def _get_chum_key(gpg):
    print "Select somebody to send to:"
    keys = gpg.list_keys(False)
    for n, key in enumerate(keys):
        print "%02d> %s (%s)" % (n, key["uids"][0], key["keyid"])
    inp = int(raw_input("Enter ID number> "))
    return keys[inp]


def _connect():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("firehose.shishnet.org", 9988))
    return s


def main_send(gpg, s, my_key, chum_key):
    while True:
        data = raw_input("Send to %s> " % chum_key["uids"][0])
        data = gpg.encrypt(data, chum_key["keyid"], sign=my_key["keyid"], passphrase="firehose", always_trust=True)
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
    gpg = gnupg.GPG()  # gnupghome="./gpg/", verbose=False)

    try:
        my_key = _get_my_key(gpg)
        my_chum_key = _get_chum_key(gpg)

        s = _connect()
        recv = threading.Thread(target=main_recv, args=(gpg, s))
        recv.daemon = True
        recv.start()
        main_send(gpg, s, my_key, my_chum_key)
    except EOFError, KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))

