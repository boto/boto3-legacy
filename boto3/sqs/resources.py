import boto3


# FIXME: These should be just sane defaults, but they are configured at
#        import-time. :/
QueueCollection = boto3.session.get_collection('sqs', 'QueueCollection')
MessageCollection = boto3.session.get_collection('sqs', 'MessageCollection')
Queue = boto3.session.get_resource('sqs', 'Queue')
Message = boto3.session.get_resource('sqs', 'Message')
