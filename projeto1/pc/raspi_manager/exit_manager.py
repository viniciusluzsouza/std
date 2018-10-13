import zmq

context = zmq.Context()
p = "tcp://localhost:40007"
s = context.socket(zmq.REQ)
s.connect(p)

s.send_json({'cmd': 0})	# CMD to exit
resp = s.recv_json()