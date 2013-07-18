from boto3.base import BotoObject


class Queue(BotoObject):
    service_name = 'sqs'
    _json_name = 'Queue'


class Message(BotoObject):
    service_name = 'sqs'
    _json_name = 'Message'
