#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
import json

class ServicesPublisher(object):
	"""docstring for ServicePublisher"""
	def __init__(self, ip, port, hostname):
		self.services = []
		self.json_msg_obj = {'hostname': hostname, 'services': self.services}
		self.context = zmq.Context()
		self.sock = self.context.socket(zmq.PUB)
		self.p = "tcp://" + str(ip) + ":" + str(port)
		self.sock.bind(self.p)


	def register_service(self, service):
		if service not in self.services:
			self.services.append(service)

	def delete_service(self, service):
		if service in self.services:
			self.services.remove(service)

	def pub_services(self):
		msg = "RASPI_SERVICES " + json.dumps(self.json_msg_obj)
		print("sending: %s" % str(msg))
		self.sock.send(msg.encode())
