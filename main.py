import websocket
import _thread
import time
import json
from termcolor import colored
from functools import reduce
import math
import numpy as np

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
		
		def check_origin(self, origin):
			return True

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
	book[symbol] = {'ask': {}, 'bid': {}, 'trade': {}}
	conn = yield websocket_connect("wss://api2.poloniex.com/")
	conn.write_message(json.dumps({'command':'subscribe','channel': symbol}))
	while True:
		msg = yield conn.read_message()
		if msg is None: break
		payload = json.loads(msg)

		orders = payload[2] if len(payload) > 2 else payload[1] if len(payload) > 1 else []
		for order in orders:
			if order[0] is 'o':
				[trade_or_order, update_type, price, quant] = order
				bid_or_ask = 'bid' if update_type else 'ask'
				if quant == '0.00000000':
					book[symbol][bid_or_ask].pop(price, None)
				else:
					book[symbol][bid_or_ask][price] = quant
			elif order[0] is 'i':
				[trade_or_order, inner_book] = order
				book[symbol]['ask'] = inner_book['orderBook'][0]
				book[symbol]['bid'] = inner_book['orderBook'][1]
				pass
			elif order[0] is 't':
				[trade_or_order, _id, update_type, price, quant, timestamp] = order
				book[symbol]['trade'][price] = quant
			else:
				print(order)
				pass

		# NOT PRECISE
		VWAP_TRUNCATE = 10

		def vwap(od):
			q = np.asarray(
				list(map(float, list(od.values())[:VWAP_TRUNCATE]))
			)
		
			p = np.asarray(
				list(map(float, list(od)[:VWAP_TRUNCATE]))
			)

			vwap = np.sum(p * q) / np.sum(q)
			return vwap

		ask = OrderedDict(sorted(book[symbol]['ask'].items(), key=lambda t: t[0]))
		bid = OrderedDict(sorted(book[symbol]['bid'].items(), key=lambda t: t[0], reverse=True))

		trade = OrderedDict(sorted(book[symbol]['trade'].items(), key=lambda t: t[0]))

		book[symbol]['vwap'] = {'truncate': VWAP_TRUNCATE, 'vwap_ask': vwap(ask), 'vwap_bid': vwap(bid)}
		book[symbol]['trade'] = trade
		book[symbol]['ask'] = ask
		book[symbol]['bid'] = bid
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
		yield [publisher.publish(), generate_feed(publisher, 'ETH_ZRX'), generate_feed(publisher, 'BTC_ZRX'), generate_feed(publisher, 'BTC_ETH')]

if __name__ == "__main__":
		IOLoop.instance().run_sync(main)