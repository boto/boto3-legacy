import hashlib

from boto3.utils import json


def subscribe_sqs_queue(sns_conn, sqs_conn, topic_arn, queue_url, queue_arn):
    """
    Handles all the details around hooking up an SNS topic to a SQS queue.

    Requires a previously created SNS topic & a previously created SQS queue.

    Specifically, this method does the following:

    * creates the subscription
    * checks for an existing policy
    * if there's no policy for the given topic/queue combination, it creates
      a policy allowing ``SendMessage``
    * finally, it updates the policy & returns the output

    :param sns_conn: A ``Connection`` subclass for SNS
    :type sns_conn: A <boto3.core.connection.Connection> subclass

    :param sqs_conn: A ``Connection`` subclass for SQS
    :type sqs_conn: A <boto3.core.connection.Connection> subclass

    :param topic_arn: The ARN for the topic
    :type topic_arn: string

    :param queue_url: The URL for the queue
    :type queue_url: string

    :param queue_arn: The ARN for the queue
    :type queue_arn: string
    """
    to_md5 = topic_arn + queue_arn
    sid = hashlib.md5(to_md5.encode('utf-8')).hexdigest()
    sid_exists = False
    resp = sns_conn.subscribe(
        topic_arn=topic_arn,
        protocol='sqs',
        notification_endpoint=queue_arn
    )
    attr = sqs_conn.get_queue_attributes(
        queue_url=queue_url,
        attribute_names=['Policy']
    )
    policy = {}

    if 'Policy' in attr:
        policy = json.loads(attr['Policy'])

    policy.setdefault('Version', '2008-10-17')
    policy.setdefault('Statement', [])

    # See if a Statement with the Sid exists already.
    for s in policy['Statement']:
        if s['Sid'] == sid:
            sid_exists = True

    if not sid_exists:
        statement = {
            'Action': 'SQS:SendMessage',
            'Effect': 'Allow',
            'Principal': {
                'AWS': '*',
            },
            'Resource': queue_arn,
            'Sid': sid,
            'Condition': {
                'StringLike': {
                    'aws:SourceArn': topic_arn,
                },
            },
        }
        policy['Statement'].append(statement)

    sqs_conn.set_queue_attributes(
        queue_url=queue_url,
        attributes={
            'Policy': json.dumps(policy)
        }
    )
    return resp
