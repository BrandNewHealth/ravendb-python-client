from connection.requests_factory import HttpRequestsFactory
from data.indexes import IndexDefinition
import unittest
import sys
import os

sys.path.append(os.path.abspath(__file__ + "/../../"))

from pyravendb.d_commands import database_commands
from pyravendb.data.database import DatabaseDocument


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_url = "http://localhost:8081"
        cls.default_database = "NorthWindTest"
        cls.db = database_commands.DatabaseCommands(HttpRequestsFactory(cls.default_url, cls.default_database))
        cls.db.admin_commands.create_database(DatabaseDocument(cls.default_database, {"Raven/DataDir": "test"}))
        cls.index_map = ("from doc in docs "
                         "select new{"
                         "Tag = doc[\"@metadata\"][\"Raven-Entity-Name\"],"
                         "LastModified = (DateTime)doc[\"@metadata\"][\"Last-Modified\"],"
                         "LastModifiedTicks = ((DateTime)doc[\"@metadata\"][\"Last-Modified\"]).Ticks}"
                         )
        cls.index = IndexDefinition(cls.index_map)
        cls.db.put_index("Testing", cls.index, True)

    @classmethod
    def tearDownClass(cls):
        cls.db.admin_commands.delete_database("NorthWindTest", True)