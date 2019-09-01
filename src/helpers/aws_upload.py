
import os
import boto3
from botocore.client import Config
S3_BUCKET                 = os.environ.get("AWS_BUCKET_NAME")
S3_KEY                    = os.environ.get("AWS_ACCESS_KEY")
S3_SECRET                 = os.environ.get("AWS_SECRET_ACCESS_KEY")
S3_LOCATION               = 'http://{}.s3.amazonaws.com/'.format(S3_BUCKET)

s3 = boto3.client(
   "s3",
   aws_access_key_id=S3_KEY,
   aws_secret_access_key=S3_SECRET,
   config=Config(signature_version='s3v4', s3={'addressing_style': 'path'}),
   region_name='ap-south-1'

)

def upload_to_aws(local_file, s3_file, bucket=S3_BUCKET, acl="authenticated-read"):
    # Use Filename as S3 FileName Key
    #s3_file = os.path.basename(local_file)
    try:
        s3.upload_file(local_file, bucket, s3_file,ExtraArgs={
                "ACL": acl,
                "ContentType": "image/png",
                'ServerSideEncryption': "AES256",
                'StorageClass': 'STANDARD_IA'
            })
        print("Upload Successful:")
        print("{}{}".format(S3_LOCATION, s3_file))
        return True
    except FileNotFoundError:
        print("The file was not found")
        return False
    except NoCredentialsError:
        print("Credentials not available")
        return False


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    try:
        response = s3.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except Exception as e:
        print(e)
        return None

    # The response contains the presigned URL
    return response