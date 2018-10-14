#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zmq
import json
import subprocess

class IPPublisher(object):
	"""IP Publisher for Raspberry PI"""

	def __init__(self, host, port, hostname, rasp_port):
		self.context = zmq.Context()
		self.p = "tcp://"+ str(host) +":"+ str(port)
		self.sock = self.context.socket(zmq.REQ)
		self.ip = self.get_ip()
		print("IP ADDRESS: %s" % self.ip)
		self.json_msg_obj = {'hostname': hostname, 'ip': self.ip, 'port': rasp_port}

	def get_ip(self):
		# Don't know a beautiful way to get ip address :'(
		ifcfg = subprocess.Popen(('ifconfig'), stdout=subprocess.PIPE)
		ifcfg = subprocess.check_output(('grep', 'inet '), stdin=ifcfg.stdout)
		ip = ifcfg.split()[1]
		return ip

	def send_ip(self):
		self.sock.connect(self.p)
		self.sock.send(json.dumps(self.json_msg_obj))
		resp = self.sock.recv()
		resp = json.loads(resp)

		return resp.get('ack', 0)