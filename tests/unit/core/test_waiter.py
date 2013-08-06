from boto3.core.waiter import Waiter

from tests import unittest


def simple_gen():
    # This is gross.
    if not hasattr(simple_gen, '_counter'):
        simple_gen._counter = -1
        simple_gen._messages = []

    simple_gen._counter += 1

    if simple_gen._counter == 0:
        simple_gen._messages.append("Nope.")
        return False
    elif simple_gen._counter == 1:
        simple_gen._messages.append("Yup.")
        return True
    else:
        # Should never get here.
        simple_gen._messages.append("wat")
        return False


class Complex(object):
    def __init__(self):
        self.fails = 0

    def request(self, url, timeout=60):
        # Simulate a failsome network.
        self.fails += 1

        if self.fails < 2:
            return False

        return "Got a 200 from %s in less than %s seconds." % (url, timeout)


def before_running(waiter_obj):
    waiter_obj.messages.append(
        "About to attempt '%s'..." % waiter_obj.target.__name__
    )


def before_sleeping(waiter_obj):
    waiter_obj.messages.append(
        "Whelp, that didn't work. Sleeping for %s..." % waiter_obj.interval
    )


class WaiterTestCase(unittest.TestCase):
    def test_simple(self):
        simple_gen._messages = []
        self.assertEqual(simple_gen._messages, [])
        waiter = Waiter(simple_gen, interval=1)
        waiter.join()
        self.assertEqual(simple_gen._messages, [
            'Nope.',
            'Yup.',
        ])

    def test_complex(self):
        client = Complex()
        waiter = Waiter(
            client.request,
            args=['http://aws.amazon.com/'],
            kwargs={'timeout': 5},
            retries=1,
            interval=0.5
        )
        waiter.messages = []
        final = waiter.join(
            before_attempt=before_running,
            before_wait=before_sleeping
        )
        self.assertEqual(waiter.messages, [
            "About to attempt 'request'...",
            "Whelp, that didn't work. Sleeping for 0.5...",
            "About to attempt 'request'..."
        ])
        self.assertEqual(
            final,
            'Got a 200 from http://aws.amazon.com/ in less than 5 seconds.'
        )


if __name__ == "__main__":
    unittest.main()
