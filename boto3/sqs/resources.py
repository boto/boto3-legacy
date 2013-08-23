from hashlib import md5

from boto3.core.resource import Resource, Structure, BoundField
from boto3.core.session import Session


class Queue(Resource):
    name = BoundField('QueueName')
    url = BoundField('QueueUrl', required=False)

    # Option #1: Big ol' dict?
    #   + Simple
    #   + Less Django-esque (hi haters)
    #   + Easy to update in subclasses
    #   - Providing callables is more difficult
    #   - It's almost all the same data each time
    #   - Nesting
    methods = {
        'create': {
            'conn_method': 'create_queue',
        },
        'delete': {
            'conn_method': 'delete_queue',
        },
        'get_url': {
            'conn_method': 'get_queue_url',
        },
        'add_permission': {
            # FIXME: Do we need params? Or can we figure this from whatever's
            #        introspected & not bound?
            'params': {
                'label': {
                    'required' True,
                    #...?
            }
        },
        'get_messages': {
            'conn_method': 'receive_message',
            'params': {
                ''
            }
        }
    }
    class_methods = {
        'list_queues': {
            'conn_method': 'list_queues',
            'params': {
                'prefix': {
                    'required': False,
                }
            }
        }
    }

    # Option #2: Declarative methods?
    #   + Feels decent
    #   + More compact
    #   + Perhaps more extensible?
    #   - Metaclasses
    #   - Changing the method list might be hard in subclasses
    create = InstanceMethod('create_queue')
    delete = InstanceMethod('delete_queue')
    list_queues = ClassMethod('list_queues', kwargs={
        'prefix': None
    })
    get_url = InstanceMethod('get_queue_url')
    get_messages = InstanceMethod('receive_message', )


class Attribute(Structure):
    name = BoundField('Name')
    value = BoundField('Value')


class Message(Structure):
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
