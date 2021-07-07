from requests_aws4auth import AWS4Auth
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import uuid
from datetime import datetime, timezone, timedelta
import time
import random
import os
from elasticsearch.client import IndicesClient

region = "ap-northeast-1" 
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

ENDPOINT = os.environ.get("ES_ENDPOINT")
INDEX = os.environ.get("ES_CODE_INDEX")
TYPE = "doc"

region = "ap-northeast-1"
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key,
                   credentials.secret_key,
                   region,
                   service,
                   session_token=credentials.token)

es = Elasticsearch(
    hosts=[{"host": ENDPOINT, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

client = IndicesClient(es)

text = '''
    const trigger_function = new PythonFunction(this, "Trigger", {
      entry: "lambda/s3-blog-trigger",
      index: "main.py",
      handler: "lambda_handler",
      runtime: lambda.Runtime.PYTHON_3_8,
      environment: {
        BUCKET_NAME: bucket.bucketName
      }
    })
'''

body = {
  "tokenizer": "standard",
  "text": text
}

res = client.analyze(body=body)

for token in res["tokens"]:
    print("{}".format(token["token"]))


print(res)
