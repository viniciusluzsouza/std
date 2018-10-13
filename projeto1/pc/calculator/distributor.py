import zmq

class Distributor(object):
	"""docstring for Distributor"""

	def __init__(self, host, port):
		self.pD = "tcp://" + host + ":" + port
		self.context = zmq.Context()
		self.sock = self.context.socket(zmq.PUSH)
		self.sock.bind(self.pD)

	def send_jobs(self, jobs):
		for job in jobs:
			self.sock.send_json(job)