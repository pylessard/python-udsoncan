from test.UdsTest import UdsTest
import threading
import queue
import _thread as thread

#Class borrowed from Python Socket test suite.
class ThreadableTest(UdsTest):
	def __init__(self, *args, **kwargs):
		UdsTest.__init__(self, *args, **kwargs)
		# Swap the true setup function
		self.__setUp = self.setUp
		self.__tearDown = self.tearDown
		self.setUp = self._setUp
		self.tearDown = self._tearDown

	def serverExplicitReady(self):
		self.server_ready.set()

	def _setUp(self):
		self.server_ready = threading.Event()
		self.client_ready = threading.Event()
		self.done = threading.Event()
		self.queue = queue.Queue(1)
		self.server_crashed = False

		# Do some munging to start the client test.
		methodname = self.id()
		i = methodname.rfind('.')
		methodname = methodname[i+1:]
		test_method = getattr(self, '_' + methodname)
		self.client_thread = thread.start_new_thread(self.clientRun, (test_method,))

		try:
			self.__setUp()
		except:
			self.server_crashed = True
			raise
		finally:
			self.server_ready.set()
		self.client_ready.wait()

	def _tearDown(self):
		self.__tearDown()
		self.done.wait()

		if self.queue.qsize():
			exc = self.queue.get()
			raise exc

	def clientRun(self, test_func):
		self.server_ready.wait()
		try:
			self.clientSetUp()
		except BaseException as e:
			self.queue.put(e)
			self.client_ready.set()
			self._clientTearDown()
			return
		finally:
			self.client_ready.set()

		if self.server_crashed:
			self._clientTearDown()
			return
		if not hasattr(test_func, '__call__'):
			raise TypeError("test_func must be a callable function")
		try:
			test_func()
		except BaseException as e:
			self.queue.put(e)
		finally:
			self._clientTearDown()

	def clientSetUp(self):
		raise NotImplementedError("clientSetUp must be implemented.")

	def _clientTearDown(self):
		self.done.set()
		try:
			if hasattr(self, 'clientTearDown'):
				self.clientTearDown()
		except BaseException as e:
			self.queue.put(e)
		finally:			
			thread.exit()