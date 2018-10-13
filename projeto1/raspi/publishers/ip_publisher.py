#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
import json

class IPPublisher(object):
	"""IP Publisher for Raspberry PI"""

	def __init__(self, host, port, hostname, ip, rasp_port):
		self.context = zmq.Context()
		self.p = "tcp://"+ str(host) +":"+ str(port)
		self.sock = self.context.socket(zmq.REQ)
		self.json_msg_obj = {'hostname': hostname, 'ip': ip, 'port': rasp_port}

	def send_ip(self):
		self.sock.connect(self.p)
		self.sock.send(json.dumps(self.json_msg_obj))
		resp = self.sock.recv()
		resp = json.loads(resp)

		return resp.get('ack', 0)
