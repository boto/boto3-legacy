from boto3.core.proxy import Proxy

from tests import unittest


class Sorter(object):
    abc = 'def'

    def sort(self, collection, *args, **kwargs):
        return sorted(collection, **kwargs)


class ProxyTestCase(unittest.TestCase):
    def setUp(self):
        super(ProxyTestCase, self).setUp()
        self.sorter = Sorter()
        self.data = [
            ('a', 2),
            ('b', 4),
            ('c', 1),
        ]

    def test_init(self):
        proxy = Proxy(self.sorter, kwargs={'key': 'abc'})
        self.assertEqual(proxy.target, self.sorter)
        self.assertEqual(proxy.args, [])
        self.assertEqual(proxy.kwargs, {
            'key': 'abc',
        })

    def test_callable_attr(self):
        proxy = Proxy(self.sorter, kwargs={'key': 'abc'})
        sort = proxy.sort
        self.assertEqual(sort, proxy)
        self.assertEqual(proxy.target, self.sorter.sort)

    def test_plain_attr(self):
        proxy = Proxy(self.sorter, kwargs={'key': 'abc'})
        self.assertEqual(proxy.abc, 'def')

    def test_call(self):
        proxy = Proxy(self.sorter, kwargs={'key': lambda x: x[1]})

        # Add additional args.
        results = proxy.sort(self.data, reverse=True)
        self.assertEqual(results, [
            ('b', 4),
            ('a', 2),
            ('c', 1),
        ])

    def test_call_no_args(self):
        proxy = Proxy(self.sorter, kwargs={'key': lambda x: x[1]})

        # Plain usage.
        results = proxy.sort(self.data)
        self.assertEqual(results, [
            ('c', 1),
            ('a', 2),
            ('b', 4),
        ])

    def test_call_override_args(self):
        proxy = Proxy(self.sorter, kwargs={'key': lambda x: x[1]})

        # Override a proxied argument.
        results = proxy.sort(self.data, key=lambda x: x[0])
        self.assertEqual(results, [
            ('a', 2),
            ('b', 4),
            ('c', 1),
        ])
