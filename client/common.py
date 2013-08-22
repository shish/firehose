
import gnupg


__version__ = "0.0.0"


def uid_to_name(uid):
    return uid.partition("(")[0].partition("<")[0].strip()


class Chum(object):
    def __init__(self, key):
        self.name = uid_to_name(key["uids"][0])
        self.uid = key["uids"][0]
        self.keyid = key["keyid"]


class FHC(object):
    def __init__(self):
        self.gpg = gnupg.GPG()

    def get_chums(self):
        return [Chum(key) for key in self.gpg.list_keys(False)]

    def get_identities(self):
        return [Chum(key) for key in self.gpg.list_keys(True)]


ANONYMOUS = Chum({"keyid": None, "uids": ["Anonymous"]})
