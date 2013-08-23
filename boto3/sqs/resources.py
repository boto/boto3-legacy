from hashlib import md5

from boto3.core.exceptions import MD5ValidationError
from boto3.core.resource import Resource, Structure
from boto3.core.resource import BoundField, ListBoundField
from boto3.core.resource import InstanceMethod, ClassMethod


class Queue(Resource):
    # A special, required key identifying what API versions a given
    # ``Resource/Structure`` works correctly with.
    valid_api_versions = [
        '2012-11-05',
    ]

    # Instance variables
    name = BoundField('QueueName')
    url = BoundField('QueueUrl', required=False)

    # Methods
    create = InstanceMethod('create_queue')
    delete = InstanceMethod('delete_queue')
    list_queues = ClassMethod('list_queues', kwargs={
        'prefix': None
    })
    get_url = InstanceMethod('get_queue_url')
    get_messages = InstanceMethod('receive_message', )


class Attribute(Structure):
    valid_api_versions = [
        '2012-11-05',
    ]

    name = BoundField('Name')
    value = BoundField('Value')


class Message(Structure):
    valid_api_versions = [
        '2012-11-05',
    ]

    body = BoundField('Body')
    md5 = BoundField('MD5OfBody', required=False)
    message_id = BoundField('MessageId', required=False)
    receipt_handle = BoundField('ReceiptHandle', required=False)
    attributes = ListBoundField('Attribute', Attribute)

    def post_populate(self):
        # Verify the MD5 if present.
        if not self.md5:
            return

        body_md5 = md5(self.body).hexdigest()

        if body_md5 != self.md5:
            raise MD5ValidationError("The provided MD5 does not match the body")
