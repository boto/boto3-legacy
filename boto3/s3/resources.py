import io

import boto3
from boto3.core.resources import Resource


class S3ObjectCustomizations(Resource):
    def get_content(self):
        if not 'body' in self._data:
            return None

        body = self._data['body']

        if hasattr(body, 'seek'):
            try:
                body.seek(0)
            except io.UnsupportedOperation:
                # Some things are not rewindable. Don't die as a result.
                pass

        if hasattr(body, 'read'):
            return body.read()

        return body

    def set_content(self, content):
        # ``botocore`` handles the details, whether it's a string or a
        # file-like object. This method is mostly here for API reflection.
        self._data['body'] = content


BucketCollection = boto3.session.get_collection(
    's3',
    'BucketCollection'
)
ObjectCollection = boto3.session.get_collection(
    's3',
    'ObjectCollection'
)
ObjectVersionCollection = boto3.session.get_collection(
    's3',
    'ObjectVersionCollection'
)
Bucket = boto3.session.get_resource('s3', 'Bucket')
Object = boto3.session.get_resource(
    's3',
    'Object',
    base_class=S3ObjectCustomizations
)
ObjectVersion = boto3.session.get_resource(
    's3',
    'ObjectVersion',
)

# Keep it on the collection, not the session-wide cached version.
ObjectCollection.change_resource(Object)
