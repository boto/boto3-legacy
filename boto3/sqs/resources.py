from boto3.core.resource import Resource
from boto3.sqs.connection import SQSConnection


class SQSQueue(Resource):
    connection_class = SQSConnection
    # Upon processing this, we'll also generate a reflected version to
    # speed up processing output.
    instance_vars = {
        # instance_name: snake_case_service_name
        'name': 'queue_name',
        # ...
    }
    crud = {
        'create': 'create_queue',
        'delete': 'delete_queue',
        # In this case, there is no 'read' or 'update' methods on the
        # connection, so they stay unimplemented.
    }


class SQSMessage(Resource):
    connection_class = SQSConnection
    instance_vars = {
        # Dotted syntax allows us to refer to instance data on another
        # object...
        'queue.url': 'queue_url',
        'body': 'body',
    }
    # Added is a way to depend on a parent object.
    depends_on = {
        # instance_name: class_or_import_string
        'queue': SQSQueue,
        # Could have been ``'queue': 'boto3.sqs.resource.SQSQueue'`` to
        # mitigate circular dependencies...
    }
    crud = {
        'create': 'send_message',
        'delete': 'delete_message',
        'get': 'receive_message',
        # No ``update`` is present in the API.
    }
