from boto3.utils import json


# FIXME: From Boto v2. Perhaps this should move/be assumed elsewhere?
ASSUME_ROLE_POLICY_DOCUMENT = json.dumps({
    'Statement': [
        {
            'Principal': {
                'Service': ['ec2.amazonaws.com']
            },
            'Effect': 'Allow',
            'Action': ['sts:AssumeRole']
        }
    ]
})
