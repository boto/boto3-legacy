from __future__ import unicode_literals
import hashlib

from boto3.core.exceptions import MD5ValidationError
from boto3.core.exceptions import UnknownFieldError
from boto3.core.resources import fields
from boto3.core.resources.structures import Structure

from tests import unittest


class TestTag(Structure):
    valid_api_versions = [
        '2013-09-24',
    ]

    name = fields.BoundField('Name')


class HelloField(fields.BoundField):
    def get_python(self, instance):
        data = super(HelloField, self).get_python(instance)
        return "Hello, {0}".format(data)


class TestStructure(Structure):
    valid_api_versions = [
        '2013-09-24',
        '2013-07-31',
    ]

    name = HelloField('Name')
    slug = fields.BoundField('Slug', required=False)
    md5 = fields.BoundField('TestMD5')
    body = fields.BoundField('MessageBody')
    tags = fields.ListBoundField('Tags', TestTag)

    def prepare(self, data):
        if not data.get('slug'):
            slug = data['name'].lower()
            data['slug'] = slug
            # FIXME: This feels clumsy. :/
            self.fields['slug'].set_python(self, slug)

        return data

    def post_populate(self, data):
        if not 'MessageBody' in data:
            return data

        md5_seen = hashlib.md5(data['MessageBody'].encode('utf-8')).hexdigest()

        if md5_seen != self.md5:
            raise MD5ValidationError("Whoopsie!")

        return data


class StructureTestCase(unittest.TestCase):
    def setUp(self):
        super(StructureTestCase, self).setUp()
        self.tag_1 = TestTag(
            name='one'
        )
        self.tag_2 = TestTag(
            name='two'
        )
        self.hw_digest = '86fb269d190d2c85f6e0468ceca42a20'
        self.struct = TestStructure(
            name='test',
            md5=self.hw_digest,
            body='Hello world!',
            tags=[
                self.tag_1,
                self.tag_2
            ]
        )

    def test_init(self):
        self.assertEqual(sorted(self.struct._data.keys()), [
            'body',
            'md5',
            'name',
            'tags',
        ])

    def test_getattr(self):
        # A plain attr.
        self.struct.whatever = True
        self.assertEqual(self.struct.whatever, True)

        # A field.
        # First, the internal state.
        self.assertEqual(self.struct._data['name'], 'test')
        # Then, the post-processing by the field.
        self.assertEqual(self.struct.name, 'Hello, test')

    def test_setattr(self):
        # A plain attr.
        with self.assertRaises(AttributeError):
            self.struct.whatever

        self.struct.whatever = True
        self.assertEqual(self.struct.whatever, True)

        # A field.
        self.assertEqual(self.struct._data['name'], 'test')
        self.struct.name = 'foo'
        self.assertEqual(self.struct.name, 'Hello, foo')
        self.assertTrue(self.struct.fields['name'])

    def test_delattr(self):
        # A plain attr.
        self.struct.whatever = True
        self.assertEqual(self.struct.whatever, True)
        del self.struct.whatever

        with self.assertRaises(AttributeError):
            self.struct.whatever

        # A field.
        self.assertEqual(self.struct._data['name'], 'test')
        del self.struct.name

        with self.assertRaises(KeyError):
            self.struct._data['name']

    def test_full_prepare(self):
        data = self.struct.full_prepare()
        self.assertEqual(data, {
            'name': 'test',
            'body': 'Hello world!',
            'md5': '86fb269d190d2c85f6e0468ceca42a20',
            'slug': 'test',
            'tags': [
                {
                    'name': 'one',
                },
                {
                    'name': 'two',
                },
            ],
        })

    def test_prepare_failed(self):
        # Delete a required key.
        del self.struct.name

        with self.assertRaises(KeyError):
            data = self.struct.full_prepare()

    def test_full_populate(self):
        body = 'texty text text'
        struct = TestStructure()
        # Explicit call, rather than ``__init__`` side-effect.
        struct.full_populate({
            'Name': 'another',
            'TestMD5': hashlib.md5(body.encode('utf-8')).hexdigest(),
            'MessageBody': body,
            'Tags': [],
        })
        self.assertEqual(struct._data, {
            'body': 'texty text text',
            'md5': 'd86506a0f73a23cf8695e70ae52119ec',
            'name': 'another',
            'tags': [],
        })

    def test_populate_failed(self):
        struct = TestStructure()

        with self.assertRaises(MD5ValidationError):
            struct.full_populate({
                'Name': 'another',
                # Bad MD5 value.
                'TestMD5': 'abc123',
                'MessageBody': 'texty text text',
                'Tags': []
            })
