#!/usr/bin/env python

import base64
import sys
import logging

import firehose.common as common


class CLI(common.FirehoseClient):
    def __select(self, chums, prompt):
        print prompt
        for n, chum in enumerate(chums):
            print "%02d> %s (%s)" % (n, chum.name, chum.keyid)
        inp = raw_input("Enter ID number> ")
        return chums[int(inp)]

    def main(self, args=sys.argv):
        common.FirehoseClient.__init__(self)
        self.load_config()

        try:
            my_self = self.__select(self.get_identities(), "Select an identity to send as:")
            my_chum = self.__select(self.get_chums(), "Select somebody to send to:")

            self.set_identity(my_self)
            self.start_recv_thread()

            while True:
                data = raw_input("Send to %s> " % my_chum.name)
                cmd, _, args = data.partition(" ")
                if cmd == "/me":
                    data = "ACT " + args
                elif cmd == "/ping":
                    data = "PING 0"
                else:
                    data = "MSG " + data
                my_chum.send(data)
        except (EOFError, KeyboardInterrupt):
            pass

    def on_msg(self, chum, target, message):
        print "%s: %s" % (chum.name, message)

    def on_act(self, chum, target, message):
        print "* %s %s" % (chum.name, message)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)19.19s %(levelname)4.4s %(name)s: %(message)s")
    module_log = logging.getLogger("firehose")
    module_log.setLevel(logging.DEBUG)
    module_log = logging.getLogger("gnupg")
    module_log.setLevel(logging.INFO)
    sys.exit(CLI().main(sys.argv))

