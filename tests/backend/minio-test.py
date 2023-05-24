import boto3
from botocore.exceptions import ClientError

import urllib3
urllib3.disable_warnings()

if __name__ == '__main__':

    clientArgs = {
        'aws_access_key_id': 'clarklab',
        'aws_secret_access_key': 'rciIzOwOZ9i8u17j11IC8IdpEZdiUIdtMKnXiAp6',
        'endpoint_url': 'https://minio.uvarc.io/',
        'verify': False
    }

    client = boto3.resource("s3", **clientArgs)

    try:
        print('Retrieving buckets...')
        print()

        for bucket in client.buckets.all():
            bucket_name = bucket.name
            print('Bucket name: {}'.format(bucket_name))

            objects = client.Bucket(bucket_name).objects.all()

            for obj in objects:
                object_name = obj.key

                print('Object name: {}'.format(object_name))

            print()

    except ClientError as err:
        print("Error: {}".format(err))
