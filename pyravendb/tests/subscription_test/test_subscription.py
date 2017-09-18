import threading

from pyravendb.subscriptions.data import *
from pyravendb.commands.raven_commands import GetSubscriptionsCommand
from pyravendb.tests.test_base import TestBase
import unittest


class User:
    def __init__(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name

    def __str__(self):
        return self.first_name + " " + self.last_name


class TestSubscription(TestBase):
    def setUp(self):
        super(TestSubscription, self).setUp()
        self.results = []
        self.items_count = 0
        self.expected_items_count = None
        self.event = threading.Event()
        self.ack = threading.Event()

    def process_documents(self, batch):
        self.items_count += len(batch.items)
        for b in batch.items:
            self.results.append(b.result)
        if self.items_count == self.expected_items_count:
            self.event.set()

    def acknowledge(self, batch):
        if not self.ack.is_set():
            self.ack.set()

    def tearDown(self):
        super(TestSubscription, self).tearDown()
        self.delete_all_topology_files()
        self.event.clear()
        self.ack.clear()

    def test_create_and_run_subscription_with_object(self):
        self.expected_items_count = 2
        with self.store.open_session() as session:
            session.store(User("Idan", "Shalom"))
            session.store(User("Ilay", "Shalom"))
            session.store(User("Raven", "DB"))
            session.save_changes()

        creation_options = SubscriptionCreationOptions("FROM Users where last_name='Shalom'")
        self.store.subscription.create(creation_options)

        request_executor = self.store.get_request_executor()
        subscriptions = request_executor.execute(GetSubscriptionsCommand(0, 1))
        self.assertGreaterEqual(len(subscriptions), 1)

        connection_options = SubscriptionConnectionOptions(subscriptions[0].subscription_name)
        self.assertEqual(len(self.results), 0)
        with self.store.subscription.open(connection_options, object_type=User) as subscription:
            subscription.run(self.process_documents)
            self.event.wait()

        self.assertEqual(len(self.results), 2)
        for item in self.results:
            self.assertTrue(isinstance(item, User))

    def test_subscription_continue_to_take_documents(self):
        self.expected_items_count = 3
        with self.store.open_session() as session:
            session.store(User("Idan", "Shalom"))
            session.store(User("Ilay", "Shalom"))
            session.store(User("Raven", "DB"))
            session.save_changes()

        self.store.subscription.create("FROM Users where last_name='Shalom'")

        request_executor = self.store.get_request_executor()
        subscriptions = request_executor.execute(GetSubscriptionsCommand(0, 1))
        self.assertGreaterEqual(len(subscriptions), 1)

        connection_options = SubscriptionConnectionOptions(subscriptions[0].subscription_name)
        self.assertEqual(len(self.results), 0)
        with self.store.subscription.open(connection_options) as subscription:
            subscription.confirm_callback = self.acknowledge
            subscription.run(self.process_documents)
            self.ack.wait()

            self.assertEqual(len(self.results), 2)
            with self.store.open_session() as session:
                session.store(User("Idan", "Shalom"))
                session.save_changes()
            self.event.wait()
            self.assertEqual(len(self.results), 3)


if __name__ == "__main__":
    unittest.main()