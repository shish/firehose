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
        data_type, = struct.unpack("b", self.sock.recv(1))
        if data_type == 0:
            data_len, = struct.unpack(">h", self.sock.recv(2))
            data = ""
            while len(data) < data_len:
                data = data + self.sock.recv(data_len - len(data))
            return data
        else:
            print "Unknown data type: %r" % data_type
            self.close()
            self.connect()

    def send_data(self, data):
        self.sock.sendall(data)


