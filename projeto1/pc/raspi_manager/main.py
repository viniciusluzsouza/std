#!/usr/bin/env python
# -*- coding: utf-8 -*-
import finder_raspi, services_manager
from finder_raspi import *
from services_manager import *
from threading import Event
from time import sleep
from copy import deepcopy
import subprocess
from sys import argv

class MainClass(object):
	"""docstring for MainClass"""
	GET_HOSTS = 1
	GET_SERVICES = 2
	EXIT = 0

	def __init__(self, test=0):
		self.finder = FinderRaspi("*", 50007)
		self.finder.start()

		self.service_manager = ServicesManager(test=test)
		self.service_manager.start()

		if test:
			self.test_mode()
		else:
			self.run()


	def test_mode(self):
		global finder_lock, finded_hosts, services_lock, services
		subprocess.call(['clear'], shell=True)
		while True:
			print("####### Raspberry Manager #######")
			print("Select one option:")
			print("1) Show connected RasPI")
			print("2) Show RasPI running services")
			print("0) EXIT")
			option = input("Enter option: ")

			try:
				print("=======================")
				option = int(option)
				if option == 1:
					finder_lock.acquire()
					for host in finded_hosts:
						print("Host: %s   IP: %s   %s" % (
							host['hostname'], host['ip'], str('[UP]' if host['is_alive'] else '[DOWN]')))
					finder_lock.release()

				elif option == 2:
					services_lock.acquire()
					keys = services.keys()
					for key in keys:
						print("Host: %s" % key)
						print("Services: %s" % ','.join(services_manager.services[key]))
						print("=======================")
					services_lock.release()

				elif option == 0:
					print("Exiting ...")
					services_lock.acquire()
					finder_lock.acquire()
					finder_raspi.finder_exit = 1
					services_manager.services_exit = 1
					services_lock.release()
					finder_lock.release()
					break

				else:
					print("Unknown option")

			except:
				print("Unknown option")

			print("\n\n")

	def run(self):
		global finder_lock, finded_hosts, services_lock, services
		local_context = zmq.Context()
		local_p = "tcp://*:40007"
		local_s = local_context.socket(zmq.REP)
		local_s.bind(local_p)

		while True:
			rec = local_s.recv_json()
			if 'cmd' not in rec:
				local_s.send_json({'ack': 0, 'err': "Command (cmd) not in JSON"})
				continue

			cmd = rec['cmd']
			msg = {'ack': 1}
			if cmd == MainClass.GET_HOSTS:
				finder_lock.acquire()
				msg['hosts'] = deepcopy(finded_hosts)
				finder_lock.release()

			elif cmd == MainClass.GET_SERVICES:
				services_lock.acquire()
				msg['services'] = deepcopy(services_manager.services)
				services_lock.release()

			elif cmd == MainClass.EXIT:
				services_lock.acquire()
				finder_lock.acquire()
				finder_raspi.finder_exit = 1
				services_manager.services_exit = 1
				services_lock.release()
				finder_lock.release()
				local_s.send_json({'ack': 1})
				break

			else:
				msg['ack'] = 0
				msg['err'] = "Unknown command"

			local_s.send_json(msg)


if __name__ == '__main__':
	if len(argv) > 1:
		try:
			op = int(argv[1])
			m = MainClass(op)
		except:
			print("Invalid argument")
			exit()
	else:
		m = MainClass()