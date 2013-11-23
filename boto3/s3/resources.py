import boto3
from boto3.core.resources import Resource


class S3ObjectCustomizations(Resource):
    def get_content(self):
        if not 'body' in self._data:
            return None

        body = self._data['body']

        if hasattr(body, 'seek'):
            body.seek(0)

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
S3ObjectCollection = boto3.session.get_collection(
    's3',
    'S3ObjectCollection'
)
Bucket = boto3.session.get_resource('s3', 'Bucket')
S3Object = boto3.session.get_resource(
    's3',
    'S3Object',
    base_class=S3ObjectCustomizations
)

# Keep it on the collection, not the session-wide cached version.
S3ObjectCollection.change_resource(S3Object)
