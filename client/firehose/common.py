
import json
import os
import gnupg
import logging
import threading
import random
import base64
from Queue import Queue, Empty
from time import sleep

from firehose.net import Firehose

__version__ = "0.0.0"
log = logging.getLogger(__name__)


class Chum(object):
    def __init__(self, fhc, key):
        self.fhc = fhc
        self.name = key["uids"][0].partition("(")[0].partition("<")[0].strip()
        self.uid = key["uids"][0]
        self.keyid = key["keyid"]

    def send(self, data):
        self.fhc.send(self.uid, data)


class FirehoseClient(object):
    def __init__(self):
        self.gpg = gnupg.GPG()
        self.config = {
            "status_request": False,
            "status_broadcast": False,
            "status_respond": False,

            "msg_ack_request": False,
            "msg_ack_respond": False,

            "accept_anon": False,

            #"start_in_tray": False,
        }
        self.passphrase = "firehose"
        self.identity = ANONYMOUS
        self.status = "Available"
        self.sock = None

        self.identity = self.get_identities()[0]
        self.hose = Firehose()
        self.send_queue = Queue()

    def load_config(self):
        path = os.path.expanduser("~/.config/fhc.conf")
        if os.path.exists(path):
            data = file(path).read()
            self.config.update(json.loads(data))

    def save_config(self):
        path = os.path.expanduser("~/.config/fhc.conf")
        data = json.dumps(self.config, indent=4)
        file(path, "w").write(data)

    def get_chums(self):
        return [Chum(self, key) for key in self.gpg.list_keys(False)]

    def get_chum(self, uid):
        for c in self.get_chums() + [ANONYMOUS, STATUS]:
            if uid == c.uid:
                return c
        log.warning("Couldn't find chum: %r" % uid)
        return ANONYMOUS

    def get_identities(self):
        return [Chum(self, key) for key in self.gpg.list_keys(True)] + [ANONYMOUS, ]

    # identity
    def __get_identity(self):
        return self.__identity

    def __set_identity(self, identity):
        log.info("Setting identity to %s" % identity.uid)
        self.__identity = identity

    identity = property(__get_identity, __set_identity)

    # status
    def __get_status(self):
        return self.__status

    def __set_status(self, status):
        log.info("Setting status to %s [broadcast=%r]" % (status, self.config["status_broadcast"]))
        self.__status = status
        if self.config["status_broadcast"]:
            for chum in self.get_chums():
                self.send(chum.uid, "PONG 0 %s" % self.__status)

    status = property(__get_status, __set_status)

    def start_recv_thread(self):
        def recv():
            while True:
                data = self.hose.get_data()
                if not data:
                    break
                try:
                    data = self.gpg.decrypt(data, passphrase=self.passphrase)
                    if data:
                        log.info("IN[%s]: %s", data.username, data.data)
                        self.on_raw_data(data)
                except Exception as e:
                    log.exception("Error while decoding packet")
            self.hose.close()

        thread = threading.Thread(target=recv)
        thread.daemon = True
        thread.start()

    def on_raw_data(self, data):
        chum = self.get_chum(data.username)
        target = None
        self.on_data(chum, target, data)

    def on_data(self, chum, target, data):
        cmd, _, data = data.data.partition(" ")

        if chum == ANONYMOUS and not self.config["accept_anon"]:
            log.info("Ignoring anonymous message: %r" % data)
            return

        if cmd == "MSG":
            self.on_msg(chum, None, data)

        elif cmd == "ACT":
            self.on_act(chum, None, data)

        elif cmd == "SPAM":
            self.on_spam(chum, None, data)

        elif cmd == "PING":
            self.on_ping(chum, None, data)

        elif cmd == "PONG":
            nonce, _, status = data.partition(" ")
            self.on_pong(chum, None, nonce, status)

        else:
            log.warning("Unrecognised command from %r: %r" % (chum.name, data))

    def on_msg(self, chum, target, message):
        pass

    def on_act(self, chum, target, message):
        pass

    def on_ping(self, chum, target, message):
        pass

    def on_pong(self, chum, target, nonce, status):
        pass

    def on_spam(self, chum, target, message):
        pass

    def start_send_thread(self):
        def send():
            while True:
                try:
                    target, data = self.send_queue.get_nowait()
                except Empty:
                    target, data = self.identity.uid, "SPAM " + base64.b64encode(os.urandom(random.randint(10, 50)))
                log.info("OUT[%s]: %s", target, data)
                data = self.gpg.encrypt(data, target, sign=self.identity.keyid, passphrase=self.passphrase, always_trust=True)
                self.hose.send_data(data.data)
                sleep(5)

        thread = threading.Thread(target=send)
        thread.daemon = True
        thread.start()

    def send(self, target, data):
        self.send_queue.put((target, data))


ANONYMOUS = Chum(None, {"keyid": None, "uids": ["Anonymous"]})
STATUS = Chum(None, {"keyid": None, "uids": ["Status"]})

