import zmq

context = zmq.Context()
socket_rep = context.socket(zmq.REP)
socket_rep.bind("tcp://*:9990")
socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://*:9989")

try:
    while True:
        data = socket_rep.recv()
        print ".",
        socket_pub.send(data)
except KeyboardInterrupt:
    socket.close()
    context.term()
