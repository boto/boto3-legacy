import boto3


# FIXME: These should be just sane defaults, but they are configured at
#        import-time. :/
SnsConnection = boto3.session.get_connection('sns')
