import json
import os
import logging

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Backblaze
S3_ENDPOINT = 'https://s3.us-east-005.backblazeb2.com'
S3_KEY_ID = '0052c21d8a679860000000002'
S3_APPLICATION_KEY = 'K005ua3fyQ4r3w9hShggBakdzjwD0NA'

EXAMPLE_ENDPOINT='https://s3.us-west-002.backblazeb2.com'
EXAMPLE_KEY_ID_RO='0027464dd94917b0000000001'
EXAMPLE_APPLICATION_KEY_RO='K002WU+TkHXkksxIqI6IDa/X7dsN9Cw'
EXAMPLE_BUCKET_NAME = 'developer-b2-quick-start'  # Bucket with Sample Data **PUBLIC**

log = logging.getLogger(__name__)


def create_bucket(name, client):
    try:
        log.info(f'Trying to create s3 bucket: {name}')
        response = client.create_bucket(Bucket=name,
                                        ACL='private')
        log.info(f'Success creating s3 bucket!')
        log.debug(f"Response is: {json.dumps(response, indent=2)}")
    except client.exceptions.BucketAlreadyOwnedByYou:
        log.warning(f's3 bucket {bucket_name} already exists. Carrying on...')
    except client.exceptions.BucketAlreadyExists:
        log.warning(f'{bucket_name} already exists in another account. Carrying on.')
    except ClientError as ce:
        log.error('error', ce)


def delete_all_objects(bucket_name, resource):
    try:
        log.debug(f"Attempting to delete all objects from s3 bucket {bucket_name}")
        resource.Bucket(bucket_name).objects.all().delete()
        log.debug(f"Delete complete")
    except ClientError as ce:
        log.error('error', ce)


def delete_bucket(bucket, resource):
    try:
        log.debug(f"Attempting to delete s3 bucket {bucket}")
        resource.Bucket(bucket).delete()
        log.debug(f"Delete complete")
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'NoSuchBucket':
            log.warning(f"Unable to find bucket {bucket} in delete_bucket")
        else:
            log.error('error', ce)


def download_file(bucket, directory, local_name, key_name, b2):
    file_path = directory + '/' + local_name
    try:
        log.info(f"Downloading object with key {key_name} from s3 bucket {bucket} to file {file_path}")
        b2.Bucket(bucket).download_file(key_name, file_path)
        log.debug(f"Download complete")
    except ClientError as ce:
        log.error('error', ce)


def get_boto3_client(endpoint, key_id, secret_key):
    try:
        log.info(f"Attempting to get boto3 client")
        client = boto3.client(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret_key,
        )
        log.info(f"Client ")
        return client
    except ClientError as ce:
        log.error('error', ce)
        raise


def get_boto3_resource(endpoint, key_id, secret_key):
    try:
        log.info("Attempting to get boto3 resource")
        resource = boto3.resource(
            service_name='s3',
            endpoint_url=endpoint,
            aws_access_key_id=key_id,
            aws_secret_access_key=secret_key,
            config=Config(
                signature_version="s3v4",
            ),
        )
        log.info("Resource acquired")
        return resource
    except ClientError as ce:
        log.error('error', ce)
        raise


def list_buckets(client):
    try:
        log.debug("Attempting to list buckets given client")

        my_buckets_response = client.list_buckets()

        log.info('BUCKETS')
        for bucket_object in my_buckets_response['Buckets']:
            log.info(bucket_object['Name'])

        log.debug('FULL RAW RESPONSE:')
        log.debug(my_buckets_response)

    except ClientError as ce:
        log.error('error', ce)


def list_objects_browsable_url(bucket_name, endpoint, resource):
    try:
        log.debug("Attempting to list object browsable URLs")

        bucket_object_keys = list_object_keys(bucket_name, resource)

        return_list = []                # create empty list
        for key in bucket_object_keys:  # iterate bucket_objects
            url = "%s/%s/%s" % (endpoint, bucket_name, key) # format and concatenate strings as valid url
            return_list.append(url)     # for each item in bucket_objects append value of 'url' to list
        return return_list              # return list of keys from response

    except ClientError as ce:
        log.error('error', ce)


def list_object_keys(bucket_name, resource):
    try:
        log.info(f"Attempting to list object keys for bucket {bucket_name}")

        response = resource.Bucket(bucket_name).objects.all()

        return_list = []
        for object in response:
            return_list.append(object.key)
        return return_list

    except ClientError as ce:
        if ce.response['Error']['Code'] == 'NoSuchBucket':
            log.warning(f"Unable to find bucket {bucket_name} in list_object_keys")
            return []
        else:
            log.error('error', ce)


def upload_file(path_to_file, bucket_name, client):
    try:
        response = client.put_object(Bucket=bucket_name,
                                     Key=os.path.basename(path_to_file),
                                     Body=open(path_to_file, mode='rb'))
        log.info(f"Successful upload of file {path_to_file} to bucket {bucket_name}.")
        log.debug(json.dumps(response, indent=2))
    except client.exceptions.NoSuchBucket:
        log.error(f"Failed to upload {path_to_file} because bucket {bucket_name} doesn't exist")
    except ClientError as ce:
        log.error(f"Failed to upload {path_to_file} to bucket {bucket_name}.")
        log.error('error', ce)


if __name__ == '__main__':
    print("Hello, World!")
    logging.basicConfig(level="INFO")

    use_example = True

    if use_example:
        endpoint = EXAMPLE_ENDPOINT
        key_id = EXAMPLE_KEY_ID_RO
        secret_key = EXAMPLE_APPLICATION_KEY_RO
        bucket_name = EXAMPLE_BUCKET_NAME
    else:
        endpoint = S3_ENDPOINT
        key_id = S3_KEY_ID
        secret_key = S3_APPLICATION_KEY
        bucket_name = 'personal-finance-prod'

    boto3_resource = get_boto3_resource(endpoint, key_id, secret_key)
    boto3_client = get_boto3_client(endpoint, key_id, secret_key)

    # get list of objects in bucket
    bucket_object_keys = list_object_keys(bucket_name, boto3_resource)
    for key in bucket_object_keys:
        print(key)
    print(f"Bucket {bucket_name} contains {len(bucket_object_keys)} objects")

    # print browsable URLs
    browsable_urls = list_objects_browsable_url(bucket_name, endpoint, boto3_resource)
    for url in browsable_urls:
        print(url)
    print('\nBUCKET ', bucket_name, ' CONTAINS ', len(browsable_urls), ' OBJECTS')

    #
    print("List of buckets before attempting to delete bucket")
    list_buckets(boto3_client)

    if use_example is False:
        # Delete bucket
        delete_all_objects(bucket_name, boto3_resource)
        delete_bucket(bucket_name, boto3_resource)
        print("List of buckets after attempting to delete bucket")
        list_buckets(boto3_client)

        # create bucket
        create_bucket(bucket_name, boto3_client)
        print("List of buckets after attempting to create bucket")
        list_buckets(boto3_client)

        # download example file from internet and put it in newly created bucket
        download_file(bucket='developer-b2-quick-start',
                      directory='/Users/tegancounts/Library/CloudStorage/OneDrive-Personal/personal-finances-app',
                      local_name="foo.jpg",
                      key_name="lake.jpg",
                      b2=get_boto3_resource(EXAMPLE_ENDPOINT, EXAMPLE_KEY_ID_RO, EXAMPLE_APPLICATION_KEY_RO))

        # upload file
        upload_file(path_to_file='/Users/tegancounts/Library/CloudStorage/OneDrive-Personal/personal-finances-app/foo.jpg',
                    bucket_name=bucket_name,
                    client=boto3_client)
        print("After upload")
        bucket_object_keys = list_object_keys(bucket_name, boto3_resource)
        for key in bucket_object_keys:
            print(key)
        print(f"Bucket {bucket_name} contains {len(bucket_object_keys)} objects")

    print("Program Complete!")
