def force_delete_bucket(conn, bucket_name):
    """
    Deletes a bucket & all of it's contents.

    A convenience method added because the default ``delete_bucket`` method
    only works on **empty** buckets.

    :param conn:
    :type conn:

    :param bucket_name:
    :type bucket_name: string
    """
    marker = None
    keep_deleting = True

    while keep_deleting:
        kwargs = {}

        # botocore won't let us include this if it's ``None``.
        if marker is not None:
            kwargs['marker'] = marker

        resp = conn.list_objects(
            bucket=bucket_name,
            **kwargs
        )
        marker = resp.get('Marker', None)
        keys = [key_info['Key'] for key_info in resp.get('Contents', [])]

        # Bulk delete keys.
        if keys:
            objects = [{'Key': key} for key in keys]
            resp = conn.delete_objects(
                bucket=bucket_name,
                delete={
                    'Objects': objects
                }
            )

        if marker is None:
            keep_deleting = False

    # The bucket should now be empty.
    return conn.delete_bucket(bucket=bucket_name)
