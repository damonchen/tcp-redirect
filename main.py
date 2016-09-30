#!/usr/bin/env python
# coding=utf-8

import os
import signal
import socket
import threading
import select

port = 22
lock = threading.Lock()
total = 0

class Redirect(threading.Thread):

	def __init__(self, sock, addr):
		threading.Thread.__init__(self)
		self.sock = sock
		self.addr = addr[0]

	def run(self):
		try:
			remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			remote.connect((self.addr, port))

			fd = self.sock.fileno()
			remote_fd = remote.fileno()
			while True:
				rfds, _, efds = select.select([fd, remote_fd], [], [])
				if fd in rfds:
					data = self.sock.recv(1024)
					remote.send(data)

				if remote_fd in rfds:
					data = remote.recv(1024)
					self.sock.send(data)

				if efds:
					print 'error occur'
					break
		finally:
			self.sock.close()
			remote.close()

		try:
			lock.acquire()
			total -= 1
		finally:
			lock.release()

def handler(signum, frame):
	print 'ctrl-c'
	os.kill(os.getpid())


signal.signal(signal.SIGINT, handler)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind(('0.0.0.0', 2223))
s.listen(6)

while True:
	sock, addr = s.accept()
	print 'new socket comming', addr

	try:
		lock.acquire()
		if total >= 100:
			print 'more than 1000 connection'
			sock.close()
		total += 1
	finally:
		lock.release()

	redi = Redirect(sock, addr)
	redi.start()
