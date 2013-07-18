from boto3.utils.mangle import to_snake_case, to_camel_case

from tests import unittest


class MangleTestCase(unittest.TestCase):
    def test_to_snake_case(self):
        self.assertEqual(to_snake_case('Create'), 'create')
        self.assertEqual(to_snake_case('CreateQueue'), 'create_queue')
        self.assertEqual(to_snake_case('ThisIsReallyLong'), 'this_is_really_long')
        self.assertEqual(to_snake_case('createQueue'), 'create_queue')

    def test_to_camel_case(self):
        self.assertEqual(to_camel_case('create'), 'Create')
        self.assertEqual(to_camel_case('create_queue'), 'CreateQueue')
        self.assertEqual(to_camel_case('this_is_really_long'), 'ThisIsReallyLong')
        self.assertEqual(to_camel_case('Terrible_Snake_Case'), 'TerribleSnakeCase')


if __name__ == "__main__":
    unittest.main()
