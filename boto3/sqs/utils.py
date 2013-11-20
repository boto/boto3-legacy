def convert_queue_url_to_arn(conn, url):
    """
    Given a queue's URL, returns the ARN for that queue.

    :param conn: The SQS connection
    :type conn: A <boto3.core.connection.Connection> subclass

    :param url: The URL for the queue
    :type url: string

    :returns: The ARN for the queue
    :rtype: string
    """
    url_bits = url.split('/')[-2:]
    return 'arn:aws:sqs:{0}:{1}:{2}'.format(
        conn.region_name,
        url_bits[0],
        url_bits[1],
    )
