import path
import unittest
from mds import MongoConfig


class TestMongoConfig(unittest.TestCase):

	def setUp(self):
		# check that a local mongo docker container exists
		# docker_client = docker.from_env()

		# container_list = docker_client.containers.list()
		# mongo_available = False

		# for container in container_list:
		# 	container.name
		pass

	def test_client_creation(self):

		client = MongoConfig().connect()
		pass

	def test_connection_local(self):
		# make sure connection exists and can be reached
		client = MongoConfig().connect()
		client.ping()


	def tearDown(self):
		pass