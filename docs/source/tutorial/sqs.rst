==========================
Simple Queue Service (SQS)
==========================


Convenience API
===============

Sample::

    from boto3.sqs import Queue, Message

    # Familiar-looking Python.
    queue = Queue(name='my_test_queue').create()
    # Stored an instance variable.
    print(queue.name)
    # Received from the service.
    print(queue.queue_url)

    for i in range(5):
        message = Message(body='This is message {0}.'.format(i))
        queue.add(message)

        # An alternate relations version might look like:
        queue.messages.create(body='This is message {0}.'.format(i))

    while queue.count():
        message = queue.get()
        print(message.body)

    # An alternate relations version might look like:
    for message in queue.messages.all():
        print(message.body)

    queue.delete()


Resource API
============

Sample::

    from boto3.sqs.resources import SQSQueue, SQSMessage

    queue = SQSQueue.create(name='my_test_queue')
    msg = SQSMessage(
        body='This is an example message.'
    )
    queue.send_message(msg)

    read = queue.receive_message()
    print(read.body)

    queue.delete()


Connection API
==============

Sample::

    from boto3.core.session import Session

    session = Session()
    SQSConnection = session.get_service('sqs')

    conn = SQSConnection(region_name='us-west-2')
    q_details = conn.create_queue(queue_name='my_test_queue')

    queue_url = q_details['QueueUrl']
    print("Queue URL is: {0}".format(queue_url))

    conn.send_message(
        queue_url=queue_url,
        message_body='This is an example message.'
    )

    read = conn.receive_message(
        queue_url=queue_url,
        max_number_of_messages=1
    )
    print(read['Messages'][0]['Body'])

    conn.delete_queue(queue_url=queue_url)
