import boto3
import os
import re
from datetime import date
import json
import requests
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from pprint import pprint

'''
このプログラムがやること

定期的に呼び出されてS3にある記事の内容を
ElasticSearchのindexとして追加する。
'''

REGION = "ap-northeast-1" 
SERVICE = "es"
CREDENTIALS = boto3.Session().get_credentials()
AWSAUTH = AWS4Auth(CREDENTIALS.access_key, CREDENTIALS.secret_key, REGION, SERVICE, session_token=CREDENTIALS.token)

ENDPOINT = os.environ.get("ES_ENDPOINT")
INDEX = os.environ.get("ES_INDEX")
TYPE = "doc"

es = Elasticsearch(
    hosts=[{"host": ENDPOINT, "port": 443}],
    http_auth=AWSAUTH,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

BUCKET_NAME = os.environ.get('BUCKET_NAME')
KEY_PREFIX = os.environ.get('KEY_PREFIX')

s3 = boto3.client('s3')

def es_put_article(article):
    print(article)
    if not article.get('update'):
        article['update'] = article['date']
    res = es.index(
        index=INDEX, 
        id=article['filename'], 
        body=article, 
        doc_type=TYPE
    )
    print(res)

def lambda_handler(event, context):
    print(event)

    list_response = s3.list_objects_v2(
        Bucket=BUCKET_NAME,
        Prefix=KEY_PREFIX
    )
    
    count = 0
    
    for content in list_response['Contents']:
        
        print(count)
        count += 1
        
        key = content['Key']
        
        print(key)
        
        if not key.endswith('.json'):
            print(' ----------------json----------------------- ')
            continue
        
        get_response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=key,
        )
        
        article = json.loads(get_response['Body'].read().decode('utf-8'))
        
        if 'reponame' in article:
            del article['reponame']
        
        try:
            es_put_article(article)
        except Exception as e:
            print(' --------------------------------------- ')
            print(e)
            continue
        

