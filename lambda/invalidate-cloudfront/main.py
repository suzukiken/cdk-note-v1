import boto3
import time
import os

cloudfront = boto3.client('cloudfront')
pipeline = boto3.client('codepipeline')

DISTRIBUTION_ID = os.environ.get('DISTRIBUTION_ID')

def lambda_handler(event, context):
    print(event)
    
    allFiles = ['/*']
    
    invalidation = cloudfront.create_invalidation(
        DistributionId=DISTRIBUTION_ID,
        InvalidationBatch={
            'Paths': {
                'Quantity': 1,
                'Items': allFiles
        },
        'CallerReference': str(time.time())
    })
    
    response = pipeline.put_job_success_result(
        jobId=event['CodePipeline.job']['id']
    )
    return response