from hashlib import md5

from boto3.core.exceptions import MD5ValidationError
from boto3.core.resources import fields
from boto3.core.resources import methods
from boto3.core.resources import ResourceCollection, Resource, Structure


class SQSQueueCollection(ResourceCollection):
    resource_class = 'boto3.sqs.resources.SQSQueue'
    service_name = 'sqs'
    valid_api_versions = [
        '2012-11-05',
    ]

    # FIXME: These need to return ``SQSQueue`` objects...
    list_queues = methods.InstanceMethod('list_queues')
    create = methods.InstanceMethod('create_queue')


class SQSQueue(Resource):
    service_name = 'sqs'
    # A special, required key identifying what API versions a given
    # ``Resource/Structure`` works correctly with.
    valid_api_versions = [
        '2012-11-05',
    ]

    # Assign a default collection.
    collection = SQSQueueCollection()

    # Instance variables
    name = fields.BoundField('queue_name')
    url = fields.BoundField('queue_url', required=False)

    # Instance methods
    delete = methods.InstanceMethod('delete_queue')
    get_url = methods.InstanceMethod('get_queue_url')
    send_message = methods.InstanceMethod('send_message')
    receive_message = methods.InstanceMethod('receive_message', limit=1)
    receive_messages = methods.InstanceMethod('receive_message')
    change_message_visibility = methods.InstanceMethod(
        'change_message_visibility'
    )

    add_permission = methods.InstanceMethod('add_permission')
    remove_permission = methods.InstanceMethod('remove_permission')
    get_attributes = methods.InstanceMethod('get_queue_attributes')
    set_attributes = methods.InstanceMethod('set_queue_attributes')

    send_message_batch = methods.InstanceMethod('send_message_batch')
    delete_message_batch = methods.InstanceMethod('delete_message_batch')
    change_message_visibility_batch = methods.InstanceMethod(
        'change_message_visibility_batch'
    )


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
