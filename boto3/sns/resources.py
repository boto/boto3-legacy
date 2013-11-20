import boto3


# FIXME: These should be just sane defaults, but they are configured at
#        import-time. :/
PlatformApplicationCollection = boto3.session.get_collection(
    'sns',
    'PlatformApplicationCollection'
)
PlatformEndpointCollection = boto3.session.get_collection(
    'sns',
    'PlatformEndpointCollection'
)
TopicCollection = boto3.session.get_collection(
    'sns',
    'TopicCollection'
)
SubscriptionCollection = boto3.session.get_collection(
    'sns',
    'SubscriptionCollection'
)
PlatformApplication = boto3.session.get_resource('sns', 'PlatformApplication')
PlatformEndpoint = boto3.session.get_resource('sns', 'PlatformEndpoint')
Topic = boto3.session.get_resource('sns', 'Topic')
Subscription = boto3.session.get_resource('sns', 'Subscription')
