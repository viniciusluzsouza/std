#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
import json
import subprocess
from threading import Thread, Lock, Event
from copy import deepcopy

finder_lock = Lock()
finded_hosts = []
finder_exit = 0

class FinderRaspi(Thread):
	"""docstring for FinderRaspi"""
	def __init__(self, ip, port):
		self.context = zmq.Context()
		self.p = "tcp://"+ str(ip) +":"+ str(port)

		self.sock = self.context.socket(zmq.REP)
		self.sock.setsockopt(zmq.RCVTIMEO, 2000)
		self.sock.bind(self.p)

		super(FinderRaspi, self).__init__()


	def exit(self):
		global finder_lock, finder_exit
		finder_lock.acquire()
		exit = deepcopy(finder_exit)
		finder_lock.release()
		return exit

	def is_alive_check(self):
		global finder_lock, finded_hosts
		finder_lock.acquire()
		for host in finded_hosts:
			p = subprocess.Popen(['ping', host['ip'], '-c', '2', '-i', '0.4', '-t', '1'], stdout=subprocess.PIPE)
			p.wait()
			host['is_alive'] = not p.poll()

		finder_lock.release()


	def add_new_host(self, new_host):
		global finder_lock, finded_hosts
		finder_lock.acquire()
		for host in finded_hosts:
			if host['ip'] == new_host['ip']:
				finded_hosts.remove(host)

		new_host['is_alive'] = 1
		finded_hosts.append(new_host)
		finder_lock.release()


	def run(self):
		global finder_lock, finded_hosts, finder_exit
		counter_is_alive_check = 0

		while True:
			counter_is_alive_check += 1
			if self.exit():
				break

			# Only check hosts after 5 iterations
			if counter_is_alive_check == 5:
				self.is_alive_check()
				counter_is_alive_check = 0

			try:
				message = self.sock.recv()
				message = message.decode()
				json_msg = json.loads(message)
			except:
				continue

			if 'ip' in json_msg and 'hostname' in json_msg:
				self.add_new_host(json_msg)
				self.sock.send(json.dumps({'ack': 1}))
			else:
				self.sock.send(json.dumps({'ack': 0}))