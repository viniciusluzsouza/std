from sys import argv
from distributor import Distributor
from collector import Collector
from random import randint
import zmq

class DistributedMatrixCalculator(object):
	"""docstring for MatrixCalculator"""

	def __init__(self, workers, a_n, a_m, b_n, b_m):
		self.workers = workers
		self.a_n = a_n
		self.a_m = a_m
		self.b_n = b_n
		self.b_m = b_m

	def _get_random_matrix(self, lines, columns):
		limit = 10
		matrix = []
		for _ in range(0, lines):
			column = []
			for _ in range(0, columns):
				column.append(randint(0, limit))

			matrix.append(column)

		return matrix

	def _matrix_sum(self, matrix_a, matrix_b):
		assert len(matrix_a) == len(matrix_b)
		assert len(matrix_a[0]) == len(matrix_b[0])

		result = []
		for i in range(0, len(matrix_a)):
			c = []
			for j in range(0, len(matrix_a[0])):
				c.append(matrix_a[i][j] + matrix_b[i][j])
			result.append(c)

		return result

	def _get_divide_matrix(self, matrix, l1, l2, l3, l4):
		m = []
		for i in range(l1, l2):
			c = []
			for j in range(l3, l4):
				c.append(matrix[i][j])
			m.append(c)
		return m

	def matrix_divide(self):
		A1_N = int(len(self.matrix_a)/2) if (len(self.matrix_a) % 2) == 0 else int((len(self.matrix_a)/2))+1
		A1_M = int(len(self.matrix_a[0])/2) if (len(self.matrix_a[0]) % 2) == 0 else int((len(self.matrix_a[0])/2))+1
		A2_N = A1_N
		A2_M = len(self.matrix_a[0]) - A1_M
		A3_N = len(self.matrix_a) - A1_N
		A3_M = A1_M
		A4_N = A3_N
		A4_M = A2_M

		B1_N = int(len(self.matrix_b)/2) if (len(self.matrix_b) % 2) == 0 else int((len(self.matrix_b)/2))+1
		B1_M = len(self.matrix_b[0])
		B2_N = len(self.matrix_b) - B1_N
		B2_M = B1_M

		A1 = self._get_divide_matrix(self.matrix_a, 0, A1_N, 0, A1_M)
		A2 = self._get_divide_matrix(self.matrix_a, 0, A2_N, A1_M, len(self.matrix_a[0]))
		A3 = self._get_divide_matrix(self.matrix_a, A1_N, len(self.matrix_a), 0, A3_M)
		A4 = self._get_divide_matrix(self.matrix_a, A2_N, len(self.matrix_a), A3_M, len(self.matrix_a[0]))
		B1 = self._get_divide_matrix(self.matrix_b, 0, B1_N, 0, len(self.matrix_b[0]))
		B2 = self._get_divide_matrix(self.matrix_b, B1_N, len(self.matrix_b), 0, len(self.matrix_b[0]))

		self.divided_matrices = {'A1': A1, 'A2': A2, 'A3': A3, 'A4': A4, 'B1': B1, 'B2': B2}


	def end_all(self):
		distributor = Distributor("*", "50010")
		distributor.send_jobs([{'id': 0}])

	def _create_jobs(self):
		jobs = []
		jobs.append({'id': 'A1B1', 'a': self.divided_matrices['A1'], 'b': self.divided_matrices['B1']})
		jobs.append({'id': 'A2B2', 'a': self.divided_matrices['A2'], 'b': self.divided_matrices['B2']})
		jobs.append({'id': 'A3B1', 'a': self.divided_matrices['A3'], 'b': self.divided_matrices['B1']})
		jobs.append({'id': 'A4B2', 'a': self.divided_matrices['A4'], 'b': self.divided_matrices['B2']})
		return jobs


	def _check_services(self, show=0):
		context = zmq.Context()
		p = "tcp://localhost:40007"
		s = context.socket(zmq.REQ)
		s.connect(p)

		s.send_json({'cmd': 2})	# CMD to get services
		resp = s.recv_json()

		# Show only for test
		if show:
			print("services: %s" % str(resp))


	def _get_hosts_on(self, show=0):
		context = zmq.Context()
		p = "tcp://localhost:40007"
		s = context.socket(zmq.REQ)
		s.connect(p)

		s.send_json({'cmd': 1})	# CMD to get hosts
		resp = s.recv_json()

		if show:
			for host in resp['hosts']:
				print("Host: %s   IP: %s   %s" % (
					host['hostname'], host['ip'], str('[UP]' if host['is_alive'] else '[DOWN]')))

		return len(resp['hosts'])


	def _print_matrix(self, matrix):
		for i in matrix:
			print(i)

	def _print_two_matrices(self, matrix_a, matrix_b):
		col_size = 3*len(matrix_a[0]) + 10
		lines_a = len(matrix_a)
		lines_b = len(matrix_b)
		lines = lines_a if lines_a > lines_b else lines_b
		for i in range(0, lines):
			line = ""
			if not i > lines_a-1:
				line += str(matrix_a[i]).ljust(col_size)
			else:
				line += " ".ljust(col_size)

			if not i > lines_b-1:
				line += str(matrix_b[i])

			print(line)


	def run(self):
		print("==== Checking hosts on ====")
		num_hosts = self._get_hosts_on(1)
		print("Hosts ON: %d" % num_hosts)

		print("==== Creating random matrices ====")
		self.matrix_a = self._get_random_matrix(self.a_n, self.a_m)
		self.matrix_b = self._get_random_matrix(self.b_n, self.b_m)

		print("==== Created Matrices: ====")
		self._print_two_matrices(self.matrix_a, self.matrix_b)

		self.matrix_divide()
		distributor = Distributor("*", "50010")
		collector = Collector("*", "50012", 5000)
		distributor.send_jobs(self._create_jobs())

		# For test, check services in rasp's
		self._check_services(1)

		results = collector.collect(4)

		if 'err' in results:
			print("Error in some RasPI: %s" % results['err'])
			exit()

		print("==== Appending matrices ====")
		C1 = self._matrix_sum(results['A1B1'], results['A2B2'])
		C2 = self._matrix_sum(results['A3B1'], results['A4B2'])
		C = C1 + C2

		print("==== Final result: ====")
		self._print_matrix(C)


if __name__ == "__main__":
	if len(argv) < 6:
		print("Invalid arguments. Execute with: ")
		print("calculator <works_number> <lines_A> <columns_A> <lines_B> <columns_B>")
		print("Eg. calculator 4 1000 1000 1000 1000")
		exit()

	try:
		workers = int(argv[1])
		lines_a = int(argv[2])
		columns_a = int(argv[3])
		lines_b = int(argv[4])
		columns_b = int(argv[5])
	except:
		print("Invalid arguments.")
		exit()

	if columns_a != lines_b:
		print("Only matrixes [NxM] x [MxP] can be multiply!")
		exit()

	matrix_calculator = DistributedMatrixCalculator(workers, lines_a, columns_a, lines_b, columns_b)
	print("Press Enter when the workers are ready or 'q' to close all workers: ")
	cmd = raw_input()
	if cmd.lower() == 'q':
		matrix_calculator.end_all()
	else:
		print("Initializing ...")
		matrix_calculator.run()