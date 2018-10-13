import zmq

class Collector(object):
	"""docstring for Collector"""

	def __init__(self, host, port, timeout):
		self.pC = "tcp://" + host + ":" + port
		self.context = zmq.Context()

		self.sock = self.context.socket(zmq.PULL)
		self.sock.setsockopt(zmq.RCVTIMEO, int(timeout))
		self.sock.bind(self.pC)

	def collect(self, counter):
		received_works = {}
		for _ in range(0, counter):
			try:
				w = self.sock.recv_json()
			except:
				continue

			# If an error occurs, stop all
			if ('ack' not in w) or (not w['ack']) \
				or ('id' not in w) or ('result' not in w):
				if 'err' in w:
					received_works['err'] = w['err']
				else:
					received_works['err'] = "Unkown error"
				break

			received_works.update({w['id']: w['result']})

		return received_works