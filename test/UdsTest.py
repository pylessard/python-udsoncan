import unittest
import logging
import sys

class UdsTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)
		loglevel = logging.DEBUG

		rootlogger = logging.getLogger()
		rootlogger.setLevel(loglevel)

		ch = logging.StreamHandler()
		ch.setLevel(loglevel)

		formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(name)s - %(message)s', datefmt='%H:%M:%S')
		ch.setFormatter(formatter)

		rootlogger.addHandler(ch)
