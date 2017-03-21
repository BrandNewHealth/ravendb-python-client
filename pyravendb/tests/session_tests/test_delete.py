import sys
import os

sys.path.append(os.path.abspath(__file__ + "/../"))

from pyravendb.tests.test_base import TestBase
from pyravendb.store.document_store import DocumentStore
from pyravendb.custom_exceptions import exceptions
import unittest


class Product(object):
    def __init__(self, Id=None, name=None):
        self.Id = Id
        self.name = name


class TestDelete(TestBase):
    @classmethod
    def setUpClass(cls):
        super(TestDelete, cls).setUpClass()
        cls.document_store = DocumentStore(cls.default_url, cls.default_database)
        cls.document_store.initialize()

        with cls.document_store.open_session() as session:
            session.store(Product("products/101", "test"))
            session.store(Product("products/10", "test"))
            session.store(Product("products/106", "test"))
            session.store(Product("products/107", "test"))
            session.save_changes()

    def test_delete_with_key_with_save_session(self):
        with self.document_store.open_session() as session:
            session.delete("products/101")
            session.save_changes()
            self.assertIsNone(session.load("products/101"))

    def test_delete_with_key_without_save_session(self):
        with self.document_store.open_session() as session:
            session.delete("products/10")
            self.assertIsNone(session.load("products/101"))

    def test_delete_after_change_fail(self):
        with self.document_store.open_session() as session:
            product = session.load("products/106")
            product.name = "testing"
            with self.assertRaises(exceptions.InvalidOperationException):
                session.delete("products/106")

    def test_delete_after_change_success_with_save_session(self):
        with self.document_store.open_session() as session:
            product = session.load("products/107")
            product.name = "testing"
            session.delete_by_entity(product)
            session.save_changes()
            self.assertIsNone(session.load("products/107"))


if __name__ == "__main__":
    unittest.main()