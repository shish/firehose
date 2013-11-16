import zmq



class Firehose(object):
    def __init__(self):
        self.sock_req = None
        self.sock_sub = None
        self.connect()

    def connect(self):
        self.context = zmq.Context()
        self.sock_req = self.context.socket(zmq.PUSH)
        self.sock_req.connect("tcp://firehose.shishnet.org:9990")
        self.sock_sub = self.context.socket(zmq.SUB)
        self.sock_sub.connect("tcp://firehose.shishnet.org:9989")
        self.sock_sub.setsockopt(zmq.SUBSCRIBE, "")

    def close(self):
        self.sock_sub.close()
        self.sock_req.close()
        self.context.term()
        self.sock = None

    def get_data(self):
        return self.sock_sub.recv()

    def send_data(self, data):
        print "Sending data"
        self.sock_req.send(data)
