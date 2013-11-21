import boto3


# FIXME: These should be just sane defaults, but they are configured at
#        import-time. :/
BucketCollection = boto3.session.get_collection(
    's3',
    'BucketCollection'
)
S3ObjectCollection = boto3.session.get_collection(
    's3',
    'S3ObjectCollection'
)
Bucket = boto3.session.get_resource('s3', 'Bucket')
S3Object = boto3.session.get_resource('s3', 'S3Object')
