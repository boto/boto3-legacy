from __future__ import unicode_literals
from hashlib import md5

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


class TestStructure(Structure):
    valid_api_versions = [
        '2013-09-24',
        '2013-07-31',
    ]

    name = fields.BoundField('Name')
    slug = fields.BoundField('Slug', required=False)
    md5 = fields.BoundField('TestMD5')
    body = fields.BoundField('MessageBody')
    tags = fields.ListBoundField('Tags', TestTag)

    def prepare(self, data):
        if not data.get('slug'):
            slug = self.name.lower()
            data['slug'] = slug
            # FIXME: This feels clumsy. :/
            self.fields['slug'].set_python(self, slug)

        return data

    def post_populate(self, data):
        md5_seen = md5(data['body'].encode('utf-8')).hexdigest()

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

    def test_full_populate(self):
        body = 'texty text text'
        struct = TestStructure()
        # Explicit call, rather than ``__init__`` side-effect.
        struct.full_populate({
            'name': 'another',
            'md5': md5(body.encode('utf-8')).hexdigest(),
            'body': body,
            'tags': [],
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
                'name': 'another',
                # Bad MD5 value.
                'md5': 'abc123',
                'body': 'texty text text',
                'tags': []
            })

    def test_populate_extra_keys(self):
        struct = TestStructure()

        with self.assertRaises(UnknownFieldError) as cm:
            struct.full_populate({
                'this': 'is rubbish',
            })

        self.assertTrue('unknown field' in str(cm.exception))

