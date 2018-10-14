#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ip_publisher import IPPublisher
from services_publisher import ServicesPublisher
from time import sleep
import zmq
from os import sys
import subprocess


class MainPublisher(object):
	"""docstring for MainPublisher"""
	PUBLISH_IP = 1
	PUBLISH_SERVICE = 2
	DELETE_SERVICE = 3
	EXIT = 0

	def __init__(self, server, port):
		self.hostname = self.get_hostname()
		self.ip_pub = IPPublisher(host=server, port="50007", hostname=self.hostname, rasp_port=port)
		self.service_pub = ServicesPublisher(ip="*", port=port, hostname=self.hostname)

	def get_hostname(self):
		return subprocess.check_output(['hostname']).rstrip()

	def run_test(self):
		if not self.ip_pub.send_ip():
			print("Fail to send ip")

		while True:
			print(" ### Test Mode ### ")
			print("1) IP Publisher")
			print("2) Service Publisher")
			print("3) Delete a service")
			print("0) EXIT")
			cmd = raw_input("Command: ")

			try:
				cmd = int(cmd)
				if cmd == 1:
					self.ip_pub.send_ip()
				elif cmd == 2:
					service = raw_input("Service name: ")
					self.service_pub.register_service(service)
					self.service_pub.pub_services()
				elif cmd == 3:
					service = raw_input("Service to delete: ")
					self.service_pub.delete_service(service)
					self.service_pub.pub_services()
				elif cmd == 0:
					break

			except:
				print("Unknown option")


	def run(self):
		if not self.ip_pub.send_ip():
			print("Fail to send ip")

		local_context = zmq.Context()
		local_p = "tcp://*:40008"
		local_s = local_context.socket(zmq.REP)
		local_s.bind(local_p)

		while True:
			rec = local_s.recv_json()
			if 'cmd' not in rec:
				local_s.send_json({'ack': 0, 'err': "Command (cmd) not in JSON"})
				continue

			cmd = rec['cmd']
			msg = {'ack': 1}
			if cmd == MainPublisher.PUBLISH_IP:
				self.ip_pub.send_ip()

			elif cmd == MainPublisher.PUBLISH_SERVICE:
				if 'service' not in rec:
					msg['ack'] = 0
					msg['err'] = "Service to publish not in JSON"
				else:
					self.service_pub.register_service(rec['service'])
					self.service_pub.pub_services()

			elif cmd == MainPublisher.DELETE_SERVICE:
				if 'service' not in rec:
					msg['ack'] = 0
					msg['err'] = "Service to delete not in JSON"
				else:
					self.service_pub.delete_service(rec['service'])
					self.service_pub.pub_services()

			elif cmd == MainPublisher.EXIT:
				local_s.send_json({'ack': 1})
				break

			else:
				msg['ack'] = 0
				msg['err'] = "Unknown command"

			local_s.send_json(msg)


if __name__ == '__main__':
	if len(sys.argv) > 3:
		if len(sys.argv) < 4:
			print("Pass hostname and IP as param to run in test mode.")
			print("eg: python host1 10.10.10.1 50009")
			exit()
		else:
			ip = sys.argv[2]
			hostname = sys.argv[1]
			port = sys.argv[3]
			m = MainPublisher(server="localhost", port=port, hostname=hostname, ip=ip)
			m.run_test()
	else:
		# Hard coded server (here will dns-name server)
		m = MainPublisher(server="192.168.0.32", port="50008")
		m.run()



