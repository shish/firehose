
import gnupg
import socket
import base64
import logging


__version__ = "0.0.0"
log = logging.getLogger(__name__)


def uid_to_name(uid):
    return uid.partition("(")[0].partition("<")[0].strip()


class Chum(object):
    def __init__(self, fhc, key):
        self.fhc = fhc
        self.name = uid_to_name(key["uids"][0])
        self.uid = key["uids"][0]
        self.keyid = key["keyid"]

    def send(self, data):
        self.fhc.send(self.keyid, data)


class FHC(object):
    def __init__(self):
        self.gpg = gnupg.GPG()
        self.passphrase = "firehose"
        self.identity = ANONYMOUS
        self.sock = None

        self.set_identity(self.get_identities()[0])
        self.__connect()

    def __connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("firehose.shishnet.org", 9988))

    def get_chums(self):
        return [Chum(self, key) for key in self.gpg.list_keys(False)]

    def get_chum(self, uid):
        for c in self.get_chums() + [ANONYMOUS, STATUS]:
            if uid == c.uid:
                return c
        return None

    def get_identities(self):
        return [Chum(self, key) for key in self.gpg.list_keys(True)] + [ANONYMOUS, ]

    def set_identity(self, identity):
        log.info("Setting identity to %s" % identity.uid)
        self.identity = identity

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
        log.info("OUT[%s]: %s", self.identity.uid, data)
        data = self.gpg.encrypt(data, target, sign=self.identity.keyid, passphrase=self.passphrase, always_trust=True)
        self.sock.sendall(base64.b64encode(str(data.data)))


ANONYMOUS = Chum(None, {"keyid": None, "uids": ["Anonymous"]})
STATUS = Chum(None, {"keyid": None, "uids": ["Status"]})

