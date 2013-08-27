
import json
import os
import gnupg
import logging
import threading

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
        self.fhc.send(self.keyid, data)


class FHC(object):
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
        self.status = "Unknown"
        self.sock = None

        self.set_identity(self.get_identities()[0])
        self.hose = Firehose()

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
        return None

    def get_identities(self):
        return [Chum(self, key) for key in self.gpg.list_keys(True)] + [ANONYMOUS, ]

    def set_identity(self, identity):
        log.info("Setting identity to %s" % identity.uid)
        self.identity = identity

    def set_status(self, status):
        log.info("Setting status to %s [broadcast=%r]" % (status, self.config["status_broadcast"]))
        self.status = status
        if self.config["status_broadcast"]:
            for chum in self.get_chums():
                self.send(chum.uid, "PONG 0 %s" % self.status)

    def start(self, cb):
        def handle(data):
            chum = self.get_chum(data.username)
            if cb:
                cb(chum, data)

        def recv():
            while True:
                data = self.hose.get_data()
                if not data:
                    break
                try:
                    data = self.gpg.decrypt(data, passphrase=self.passphrase)
                    if data:
                        log.info("IN[%s]: %s", data.username, data.data)
                        handle(data)
                except Exception as e:
                    log.exception("Error while decoding packet")
            self.hose.close()

        thread = threading.Thread(target=recv)
        thread.daemon = True
        thread.start()

    def send(self, target, data):
        """
        TODO: add to queue rather than sending directly
        """
        self.__send(target, data)

    def __send(self, target, data):
        """
        TODO: be a thread which reads from a queue and trickles out slowly
        TODO: if queue is empty, trickle random data
        """
        #log.info("OUT[%s]: %s", self.identity.uid, data)
        log.info("OUT[%s]: %s", target, data)
        data = self.gpg.encrypt(data, target, sign=self.identity.keyid, passphrase=self.passphrase, always_trust=True)
        self.hose.send_data(data.data)


ANONYMOUS = Chum(None, {"keyid": None, "uids": ["Anonymous"]})
STATUS = Chum(None, {"keyid": None, "uids": ["Status"]})

