import zmq

context = zmq.Context()
p = "tcp://localhost:40008"
s = context.socket(zmq.REQ)
s.connect(p)

s.send_json({'cmd': 0})