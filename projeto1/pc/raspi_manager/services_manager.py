#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
import json
from time import sleep
from threading import Thread, Lock
from finder_raspi import finder_lock, finded_hosts
from copy import deepcopy

services_lock = Lock()
services = {}
services_exit = 0

class ServicesManager(Thread):
	"""docstring for ServicesManager"""

	def __init__(self, test):
		self.context = zmq.Context()
		self.sock = self.context.socket(zmq.SUB)
		self.test = test

		super(ServicesManager, self).__init__()
	

	def exit(self):
		global services_lock, services_exit
		services_lock.acquire()
		exit = deepcopy(services_exit)
		services_lock.release()
		return exit


	def run(self):
		global services_lock, services, services_exit, finder_lock, finded_hosts

		while True:
			finder_lock.acquire()
			hosts = deepcopy(finded_hosts)
			finder_lock.release()

			if self.exit():
				break

			for host in hosts:
				if self.exit():
					break

				if self.test:
					# for test, always connect in localhost
					self.p = "tcp://" + 'localhost' + ":" + host['port']
				else:
					self.p = "tcp://" + str(host['ip']) + ":" + host['port']

				try:
					self.sock.connect(self.p)
					self.sock.setsockopt(zmq.SUBSCRIBE, b"RASPI_SERVICES")
					self.sock.setsockopt(zmq.RCVTIMEO, 2000)
					msg = self.sock.recv()
					msg = msg.decode()
					msg = msg[msg.find('{'):]

					json_obj = json.loads(msg)
					if 'hostname' not in json_obj \
						or 'services' not in json_obj:
						print("Message receive in wrong format!")
						continue

					services_lock.acquire()
					services[json_obj['hostname']] = json_obj['services']
					services_lock.release()

				except:
					continue

			sleep(1)