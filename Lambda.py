import boto3
import json
import requests
import os

def lambda_handler(event, context):
    # Get the S3 bucket and object key from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    
    # Parse the filename (key)
    filename = key.split('/')[-1]
    
    # Send a request to the EC2 instance
    ec2_url = os.environ.get("EC2_IP")
    
    # Prepare the data to be sent
    data = {
        'bucket': bucket,
        'key': key,
        'filename': filename,
        'sender_email': os.environ.get("Email_id"),
        'sender_password': os.environ.get("Password"),
        'subject': os.environ.get("subject"),
        'body': os.environ.get("body")
    }
    
    response = requests.post(ec2_url, json=data)
    return {
        'statusCode': 200,
        'body': json.dumps('Request sent to EC2')
    }