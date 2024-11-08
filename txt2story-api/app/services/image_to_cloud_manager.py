import boto3
from io import BytesIO
from PIL import Image
import os

class ImageToCloudManager:
    def __init__(self, s3_bucket_name):
        self.s3_client = boto3.client('s3')
        self.s3_bucket_name = s3_bucket_name

    def upload_image_to_s3(self, image, s3_key):
        """
        Uploads an image to an S3 bucket.
        
        Parameters:
            image (Image): The image to upload.
            s3_key (str): The path/key for storing the image in S3.

        Returns:
            str: URL of the uploaded image.
        """
        with BytesIO() as output:
            image.save(output, format="PNG")
            output.seek(0)
            self.s3_client.upload_fileobj(output, self.s3_bucket_name, s3_key)
        
        return f"https://{self.s3_bucket_name}.s3.amazonaws.com/{s3_key}"
