from boto3.core.resources.fields import BoundField
from boto3.core.resources.fields import ListBoundField

from tests import unittest


class SampleObject(object):
    # Because we're testing descriptors.
    # Normally the metaclass sets the ``name``, but we do it explicitly here.
    abc = BoundField('Basic', name='abc')
    another = BoundField('Missing', name='another', required=False)

    def __init__(self, **kwargs):
        self._data = {}

        if kwargs:
            self._data = kwargs


class BoundFieldTestCase(unittest.TestCase):
    def setUp(self):
        super(BoundFieldTestCase, self).setUp()
        self.sample = SampleObject(
            abc=123,
            # Unused data.
            hello='world'
        )

    def test_simple_init(self):
        base = BoundField('Basic')
        self.assertEqual(base.name, 'unknown')
        self.assertEqual(base.is_field, True)
        self.assertEqual(base.api_name, 'Basic')
        self.assertEqual(base.required, True)

    def test_complex_init(self):
        base = BoundField('Complex', required=False)
        self.assertEqual(base.name, 'unknown')
        self.assertEqual(base.is_field, True)
        self.assertEqual(base.api_name, 'Complex')
        self.assertEqual(base.required, False)

    def test_get(self):
        # Should find data.
        self.assertEqual(self.sample.abc, 123)

        # Will miss.
        with self.assertRaises(KeyError):
            self.sample.another

    def test_set(self):
        self.assertEqual(self.sample._data['abc'], 123)
        self.sample.abc = 234
        self.assertEqual(self.sample._data['abc'], 234)

        with self.assertRaises(KeyError):
            self.sample.another

        self.sample.another = 'athing'
        self.assertEqual(self.sample.another, 'athing')

    def test_delete(self):
        self.assertEqual(self.sample._data['abc'], 123)
        del self.sample.abc

        # Gone now.
        with self.assertRaises(KeyError):
            self.sample._data['abc']


class SampleCollector(object):
    # Because we're testing descriptors.
    # Normally the metaclass sets the ``name``, but we do it explicitly here.
    name = BoundField('Name', name='name')
    samples = ListBoundField('Samples', SampleObject, name='samples')

    def __init__(self, **kwargs):
        self._data = {}

        if kwargs:
            self._data = kwargs


class ListBoundFieldTestCase(unittest.TestCase):
    def setUp(self):
        super(ListBoundFieldTestCase, self).setUp()
        self.sample_1 = SampleObject(
            abc='one'
        )
        self.sample_2 = SampleObject(
            abc='two',
            another='here'
        )
        self.collector = SampleCollector(
            name='a-test',
            samples=[
                self.sample_1,
                self.sample_2,
            ]
        )

    def test_simple_init(self):
        base = ListBoundField('Basic', SampleObject)
        self.assertEqual(base.name, 'unknown')
        self.assertEqual(base.is_field, True)
        self.assertEqual(base.is_collection, True)
        self.assertEqual(base.data_class, SampleObject)
        self.assertEqual(base.api_name, 'Basic')
        self.assertEqual(base.required, True)

    def test_complex_init(self):
        base = ListBoundField('Complex', object, required=False)
        self.assertEqual(base.name, 'unknown')
        self.assertEqual(base.is_field, True)
        self.assertEqual(base.is_collection, True)
        self.assertEqual(base.data_class, object)
        self.assertEqual(base.api_name, 'Complex')
        self.assertEqual(base.required, False)

    def test_get(self):
        # Should find data.
        self.assertEqual(self.collector.samples[0].abc, 'one')
        self.assertEqual(self.collector.samples[1].abc, 'two')
        self.assertEqual(self.collector.samples[1].another, 'here')

        # Will miss.
        with self.assertRaises(KeyError):
            self.collector.samples[0].another

    def test_set(self):
        self.assertEqual(self.collector._data['samples'][0].abc, 'one')
        self.collector.samples[0].abc = '11'
        self.assertEqual(self.collector._data['samples'][0].abc, '11')

        with self.assertRaises(KeyError):
            self.collector.samples[0].another

        self.collector.samples[0].another = 'athing'
        self.assertEqual(self.collector.samples[0].another, 'athing')

    def test_delete(self):
        self.assertEqual(len(self.collector.samples), 2)
        self.assertEqual(self.collector._data['samples'][0].abc, 'one')

        del self.collector.samples[0]
        self.assertEqual(len(self.collector.samples), 1)
        self.assertEqual(self.collector._data['samples'][0].abc, 'two')
