import zmq

class MatrixCalculator(object):
	"""docstring for MatrixCalculator"""

	def __init__(self, hostd, portd, hostc, portc):
		self.pD = "tcp://" + hostd + ":" + portd
		self.pC = "tcp://" + hostc + ":" + portc
		self.context = zmq.Context()

		self.receiver = self.context.socket(zmq.PULL)
		self.sender = self.context.socket(zmq.PUSH)


	def matrix_multiply(self, matrix_a, matrix_b):
		m = len(matrix_b)
		p = len(matrix_b[0])
		result = []

		for i in range(0, len(matrix_a)):
			column = []
			for j in range(0, p):
				sum = 0
				for k in range(0, m):
					sum += matrix_a[i][k]*matrix_b[k][j]
				column.append(sum)
			result.append(column)

		return result


	def notify_service_on(service="matrix_calculator"):
		context = zmq.Context()
		p = "tcp://localhost:40008"
		s = context.socket(zmq.REQ)
		s.connect(p)

		s.send_json({'cmd': 2, 'service': service})	# CMD to publish service
		resp = s.recv_json()


	def run(self):
		self.notify_service_on()
		self.receiver.connect(self.pD)
		self.sender.connect(self.pC)

		while True:
			rec = self.receiver.recv_json()
			print("rec: %s" % str(rec))
			msg = {}
			if 'id' not in rec:
				msg['ack'] = 0
				msg['err'] = "ID no received"
			elif 'a' not in rec \
				or 'b' not in rec:
				msg['ack'] = 0
				msg['id'] = rec['id']
				msg['err'] = "No complete arguments"
			elif len(rec['b']) != len(rec['a'][0]):
				msg['ack'] = 0
				msg['id'] = rec['id']
				msg['err'] = "Invalid matrix sizes"
			else:
				try:
					result = self.matrix_multiply(rec['a'], rec['b'])
					msg['ack'] = 1
					msg['id'] = rec['id']
					msg['result'] = result
				except:
					msg['ack'] = 0
					msg['err'] = "Unknown error"

			self.sender.send_json(msg)


if __name__ == "__main__":
	matrix_calc = MatrixCalculator('localhost', '50010', 'localhost', '50012')
	print("Waiting a job ...")
	matrix_calc.run()