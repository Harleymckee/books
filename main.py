import websocket
import _thread
import time
import json
from termcolor import colored

from collections import OrderedDict

import random
from tornado import gen
from tornado.options import options, define
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado.websocket import WebSocketHandler, WebSocketClosedError, websocket_connect
from tornado.queues import Queue

book = {}

class Publisher(object):
		"""Handles new data to be passed on to subscribers."""
		def __init__(self):
				self.messages = Queue()
				self.subscribers = set()

		def register(self, subscriber):
				"""Register a new subscriber."""
				self.subscribers.add(subscriber)

		def deregister(self, subscriber):
				"""Stop publishing to a subscriber."""
				self.subscribers.remove(subscriber)

		@gen.coroutine
		def submit(self, message):
				"""Submit a new message to publish to subscribers."""
				yield self.messages.put(message)

		@gen.coroutine
		def publish(self):
				while True:
						message = yield self.messages.get()
						if len(self.subscribers) > 0:
								# print("Pushing message {} to {} subscribers...".format(
								# 		message, len(self.subscribers)))
								yield [subscriber.submit(message) for subscriber in self.subscribers]


class MainHandler(RequestHandler):
		"""Renders the main template for displaying messages to subscribers."""
		def get(self):
				self.render('index.html')


class Subscription(WebSocketHandler):
		"""Websocket for subscribers."""
		def initialize(self, publisher):
				self.publisher = publisher
				self.messages = Queue()
				self.finished = False

		def open(self):
				print("New subscriber.")
				self.publisher.register(self)
				self.run()

		def on_close(self):
				self._close()        

		def _close(self):
				print("Subscriber left.")
				self.publisher.deregister(self)
				self.finished = True

		@gen.coroutine
		def submit(self, message):
				yield self.messages.put(message)

		@gen.coroutine
		def run(self):
				while not self.finished:
						message = yield self.messages.get()
						# print("New message: " + str(message))
						self.send(message)

		def send(self, message):
				try:
						self.write_message(dict(value=message))
				except WebSocketClosedError:
						self._close()

@gen.coroutine
def generate_feed(publisher, symbol):
	book[symbol] = {0: {}, 1: {}, 'trades': []}
	conn = yield websocket_connect("wss://api2.poloniex.com/")
	conn.write_message(json.dumps({'command':'subscribe','channel': symbol}))
	while True:
		msg = yield conn.read_message()
		if msg is None: break
		list = json.loads(msg)
		orders = list[2] if len(list) > 2 else list[1] if len(list) > 1 else []
		for order in orders:
			if order[0] is 'o':
				[trade_or_order, update_type, price, quant] = order
				if quant == '0.00000000':
					book[symbol][update_type].pop(price, None)
				else:
					book[symbol][update_type][price] = quant
			elif order[0] is 'i':
				[trade_or_order, inner_book] = order
				# book
				print('ok')
				book[symbol][0] = inner_book['orderBook'][0]
				book[symbol][1] = inner_book['orderBook'][1]
				pass
		# data = random.randint(0, 9)
		book[symbol][0] = OrderedDict(sorted(book[symbol][0].items(), key=lambda t: t[0]))
		book[symbol][1] = OrderedDict(sorted(book[symbol][1].items(), key=lambda t: t[0]))
		# print(book)
		yield publisher.submit(book)

@gen.coroutine
def main():
		define('port', default=8080)

		options.parse_command_line()

		publisher = Publisher()

		app = Application(
				[
						('/((\w*).js)', StaticFileHandler, dict(path='.')),
						('/', MainHandler),
						('/socket', Subscription, dict(publisher=publisher))
				]
		)
		app.listen(options.port)
		yield [publisher.publish(), generate_feed(publisher, 'ETH_ZRX'), generate_feed(publisher, 'BTC_ETH')]

if __name__ == "__main__":
		IOLoop.instance().run_sync(main)