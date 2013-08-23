import socket
import base64


class Firehose(object):
    def __init__(self):
        self.sock = None
        self.__connect()

    def __connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("firehose.shishnet.org", 9988))

    def close(self):
        self.sock.close()
        self.sock = None

    def get_data(self):
        return base64.b64decode(self.sock.recv(4096))

    def send_data(self, data):
        self.sock.sendall(base64.b64encode(str(data.data)))


