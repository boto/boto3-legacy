from boto3.core.resources.fields import BoundField
from boto3.core.resources.fields import ListBoundField

from tests import unittest


class SampleObject(object):
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
        # The metaclasses usually specify name. We'll fake it here.
        self.abc = BoundField('Basic', name='abc')
        self.another = BoundField('Missing', name='another', required=False)

    def test_simple_init(self):
        base = BoundField('Basic')
        self.assertEqual(base.name, 'unknown')
        self.assertEqual(base.is_field, True)
        self.assertEqual(base.api_name, 'Basic')
        self.assertEqual(base.snake_name, 'basic')
        self.assertEqual(base.required, True)

    def test_complex_init(self):
        base = BoundField('Complex', required=False)
        self.assertEqual(base.name, 'unknown')
        self.assertEqual(base.is_field, True)
        self.assertEqual(base.api_name, 'Complex')
        self.assertEqual(base.snake_name, 'complex')
        self.assertEqual(base.required, False)

    def test_get_python(self):
        # Should find data.
        self.assertEqual(self.abc.get_python(self.sample), 123)

        # Will miss.
        with self.assertRaises(KeyError):
            self.another.get_python(self.sample)

    def test_set_python(self):
        self.assertEqual(self.sample._data['abc'], 123)
        self.abc.set_python(self.sample, 234)
        self.assertEqual(self.sample._data['abc'], 234)

        with self.assertRaises(KeyError):
            self.sample._data['another']

        self.another.set_python(self.sample, 'athing')
        self.assertEqual(self.sample._data['another'], 'athing')

    def test_get_api(self):
        # Should find data.
        self.assertEqual(self.abc.get_api(self.sample), 123)

        # Will miss.
        with self.assertRaises(KeyError):
            self.another.get_api(self.sample)

    def test_set_api(self):
        self.assertEqual(self.sample._data['abc'], 123)
        self.abc.set_api(self.sample, 234)
        self.assertEqual(self.sample._data['abc'], 234)

        with self.assertRaises(KeyError):
            self.sample._data['another']

        self.another.set_api(self.sample, 'athing')
        self.assertEqual(self.sample._data['another'], 'athing')

    def test_delete(self):
        self.assertEqual(self.sample._data['abc'], 123)
        self.abc.delete(self.sample)

        # Gone now.
        with self.assertRaises(KeyError):
            self.sample._data['abc']


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
        self.collector = SampleObject(
            name='a-test',
            samples=[
                self.sample_1,
                self.sample_2,
            ]
        )
        self.samples = ListBoundField('Samples', SampleObject, name='samples')

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

    def test_get_python(self):
        # Should find data.
        self.assertEqual(self.samples.get_python(self.collector)[0]._data['abc'], 'one')
        self.assertEqual(self.samples.get_python(self.collector)[1]._data['abc'], 'two')
        self.assertEqual(
            self.samples.get_python(self.collector)[1]._data['another'],
            'here'
        )

        # Will miss.
        with self.assertRaises(KeyError):
            self.samples.get_python(self.collector)[0]._data['another']

    # FIXME: Either the semantics around this field are bad or
    #        the test implementation above doesn't reflect the actual intent
    #        (collections) very well.
    #        Either way, this is broken.
    # def test_set_python(self):
    #     self.assertEqual(self.collector._data['samples'][0].abc, 'one')
    #     self.samples.set_python(self.collector, [0].abc = '11'
    #     self.assertEqual(self.collector._data['samples'][0].abc, '11')
    #
    #     with self.assertRaises(KeyError):
    #         self.collector.samples[0].another
    #
    #     self.collector.samples[0].another = 'athing'
    #     self.assertEqual(self.collector.samples[0].another, 'athing')

    def test_delete(self):
        self.assertEqual(len(self.collector._data['samples']), 2)

        # FIXME: Again, the intent was to be able to remove offsets, not just
        #        the whole thing. Re-evaluate.
        self.samples.delete(self.collector)

        with self.assertRaises(KeyError):
            len(self.collector._data['samples'])
