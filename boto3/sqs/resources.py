from hashlib import md5

from boto3.core.exceptions import MD5ValidationError
from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import Resource, Structure


class SQSQueue(Resource):
    # A special, required key identifying what API versions a given
    # ``Resource/Structure`` works correctly with.
    valid_api_versions = [
        '2012-11-05',
    ]

    # Instance variables
    name = fields.BoundField('queue_name')
    url = fields.BoundField('queue_url', required=False)

    # Class methods
    list_queues = methods.ClassMethod('list_queues')

    # Instance methods
    create = methods.InstanceMethod('create_queue')
    delete = methods.InstanceMethod('delete_queue')
    get_url = methods.InstanceMethod('get_queue_url')
    get_messages = methods.InstanceMethod('receive_message')
    send_message = methods.InstanceMethod('send_message')


class SQSAttribute(Structure):
    valid_api_versions = [
        '2012-11-05',
    ]

    name = fields.BoundField('Name')
    value = fields.BoundField('Value')


class SQSMessage(Structure):
    valid_api_versions = [
        '2012-11-05',
    ]

    body = fields.BoundField('Body')
    md5 = fields.BoundField('MD5OfBody', required=False)
    message_id = fields.BoundField('MessageId', required=False)
    receipt_handle = fields.BoundField('ReceiptHandle', required=False)
    attributes = fields.ListBoundField('Attribute', SQSAttribute)

    def post_populate(self):
        # Verify the MD5 if present.
        if not self.md5:
            return

        body_md5 = md5(self.body).hexdigest()

        if body_md5 != self.md5:
            raise MD5ValidationError("The provided MD5 does not match the body")
