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

