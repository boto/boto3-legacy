from boto3.core.exceptions import IncorrectImportPath
from boto3.core.session import Session
from boto3.utils.import_utils import import_class

from tests import unittest


class ImportUtilsTestCase(unittest.TestCase):
    def test_import_class_empty_string(self):
        with self.assertRaises(IncorrectImportPath) as cm:
            klass = import_class('')

        self.assertTrue('Invalid Python' in str(cm.exception))

    def test_import_class_invalid_path(self):
        with self.assertRaises(IncorrectImportPath) as cm:
            klass = import_class('boto3.nosuchmodule.Nope')

        self.assertTrue('Could not import' in str(cm.exception))

    def test_import_class_invalid_class(self):
        with self.assertRaises(IncorrectImportPath) as cm:
            klass = import_class('boto3.core.session.NopeSession')

        self.assertTrue('could not find' in str(cm.exception))

    def test_import_class(self):
        klass = import_class('boto3.core.session.Session')
        self.assertEqual(klass, Session)


if __name__ == "__main__":
    unittest.main()
