import zmq
from threading import Thread
from zmq.utils.monitor import recv_monitor_message
import logging
from terminator import Terminator


class Monitor(Thread):
	def __init__(self, socket, feedID):
		Thread.__init__(self)
		self.socket = socket
		self.feedID = feedID
		self.stop = False
		self.setName("Monitor")
		self.events = {
			"EVENT_CONNECTED": zmq.EVENT_CONNECTED,
			"EVENT_CONNECT_DELAYED": zmq.EVENT_CONNECT_DELAYED,
			"EVENT_CONNECT_RETRIED": zmq.EVENT_CONNECT_RETRIED,
			"EVENT_LISTENING": zmq.EVENT_LISTENING,
			"EVENT_BIND_FAILED": zmq.EVENT_BIND_FAILED,
			"EVENT_ACCEPTED": zmq.EVENT_ACCEPTED,
			"EVENT_ACCEPT_FAILED": zmq.EVENT_ACCEPT_FAILED,
			"EVENT_CLOSED": zmq.EVENT_CLOSED,
			"EVENT_CLOSE_FAILED": zmq.EVENT_CLOSE_FAILED,
			"EVENT_DISCONNECTED": zmq.EVENT_DISCONNECTED,
			"EVENT_ALL": zmq.EVENT_ALL,
			"EVENT_MONITOR_STOPPED": zmq.EVENT_MONITOR_STOPPED,
			"EVENT_HANDSHAKE_FAILED_NO_DETAIL": zmq.EVENT_HANDSHAKE_FAILED_NO_DETAIL,
			"EVENT_HANDSHAKE_SUCCEEDED": zmq.EVENT_HANDSHAKE_SUCCEEDED,
			"EVENT_HANDSHAKE_FAILED_PROTOCOL": zmq.EVENT_HANDSHAKE_FAILED_PROTOCOL,
			"EVENT_HANDSHAKE_FAILED_AUTH": zmq.EVENT_HANDSHAKE_FAILED_AUTH}

	def run(self):
		terminator = Terminator.getInstance()
		while not terminator.isTerminating():
			try:
				msg = recv_monitor_message(self.socket)
			except:
				break
			event = msg.get("event")
			value = msg.get("value")
			endpoint = msg.get("endpoint")

			assigned = False
			for key, val in self.events.items():
				if event == val:
					assigned = True
					logging.debug(str(key) + ' ' + str(endpoint))

			if assigned is False:
				logging.error('Unknown monitor message: %s', msg)

		logging.debug('Monitor thread %s shutting down', self.feedID)
