import zmq

context = zmq.Context()
socket_pull = context.socket(zmq.PULL)
socket_pull.bind("tcp://*:9990")
socket_pub = context.socket(zmq.PUB)
socket_pub.bind("tcp://*:9989")

try:
    while True:
        data = socket_pull.recv()
        socket_pub.send(data)
except KeyboardInterrupt:
    socket_pub.close()
    socket_pull.close()
    context.term()
