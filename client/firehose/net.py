import socket
import base64
import struct


class Firehose(object):
    def __init__(self):
        self.sock = None
        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("firehose.shishnet.org", 9988))

    def close(self):
        self.sock.close()
        self.sock = None

    def get_data(self):
        data_type, data_len = struct.unpack(">bh", self.sock.recv(3))

        if data_type != 0:
            print "Unknown data type: %r" % data_type
            self.close()
            self.connect()
            return None

        data = ""
        while len(data) < data_len:
            data = data + self.sock.recv(min(data_len - len(data), 4096))
        return data

    def send_data(self, data):
        self.sock.sendall(struct.pack(">bh", 0, len(data)) + data)


