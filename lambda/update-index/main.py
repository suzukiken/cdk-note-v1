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

S3のコンテンツが更新されると呼び出される
そのコンテンツはHugoのFront Matterがついたmarkdownとなっている
そこからタイトルやタグを取り出して
それをElasticSearchのindexとして追加する。
すでに同じidがある場合は上書きする。
idはコンテンツのファイル名（S3オブジェクトのそのディレクトリ部分を除いたKeyにする）
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

tiexp = 'title = "(.+?)"'
tgexp = 'tags = \[(.+?)\]'
dtexp = 'date = "(.+?)"'
upexp = 'update = "(.+?)"'
ctexp = 'category = "(.+?)"'
coexp = '\n[+]{3}\n(.*)'

def es_put_article(article):
    print(article)
    print('----1----')
    res = es.index(
        index=INDEX, 
        id=article['filename'], 
        body=article, 
        doc_type=TYPE
    )
    print(res)

def lambda_handler(event, context):
    print(event)

    for record in event['Records']:
        if record['eventSource'] != 'aws:s3':
            continue
        if record['s3']['bucket']['name'] != BUCKET_NAME:
            continue
        
        eventname = record['eventName'].split(':')[0]
        
        if eventname == 'ObjectCreated':
            pass
        elif eventname == 'ObjectRemoved':
            continue
        else:
            continue
        
        get_response = s3.get_object(
            Bucket=record['s3']['bucket']['name'],
            Key=record['s3']['object']['key'],
        )
        
        filename = record['s3']['object']['key'].replace(KEY_PREFIX, '').replace('.md', '')

        #try:
        text = get_response['Body'].read().decode('utf-8')
        
        mat = re.search(tiexp, text)
        if mat:
            title = mat.group(1)
            
        mat = re.search(tgexp, text)
        if mat:
            found = mat.group(1)
            tags = [stg.replace('"', '').strip() for stg in found.split(",")]
            
        mat = re.search(dtexp, text)
        if mat:
            found = mat.group(1)
            dte = date.fromisoformat(found)
        
        mat = re.search(upexp, text)
        if mat:
            upd = mat.group(1)
            
        mat = re.search(ctexp, text)
        if mat:
            category = mat.group(1)
        
        mat = re.search(coexp, text, flags=re.DOTALL)
        if mat:
            fco = mat.group(1)
        
        article = {
            "filename": filename,
            "title": title,
            "category": category,
            "tags": tags,
            "date": dte,
            "update": upd,
            "content": fco,
        }
        
        es_put_article(article)
        
        #except:
        #    continue

'''
{
   "Records":[
      {
         "eventVersion":"2.1",
         "eventSource":"aws:s3",
         "awsRegion":"ap-northeast-1",
         "eventTime":"2021-06-30T12:23:18.355Z",
         "eventName":"ObjectCreated:Put",
         "userIdentity":{
            "principalId":"AWS:AIDAIRGQRKVJ6LFTAV2U2"
         },
         "requestParameters":{
            "sourceIPAddress":"18.181.87.140"
         },
         "responseElements":{
            "x-amz-request-id":"7HTDDN7NFW7H9PVP",
            "x-amz-id-2":"BsLXK9rmLZAAvtgKlk0dCsTdt/vJ4ZKZe2MO6gGyxq9QBkL6OrVI9E0OKjiBDJroikSARhPdYXp1fLzcBEwkut6G05J5tH7I"
         },
         "s3":{
            "s3SchemaVersion":"1.0",
            "configurationId":"MzAyYzg2M2QtNzZmYS00NTY0LWFlYTItNzBlOTgxODBlNjdi",
            "bucket":{
               "name":"cdknotestragestack-bucket83908e77-15iapvi94z1g2",
               "ownerIdentity":{
                  "principalId":"A3IE8ALDKUHMWU"
               },
               "arn":"arn:aws:s3:::cdknotestragestack-bucket83908e77-15iapvi94z1g2"
            },
            "object":{
               "key":"articles/cdk-fargate.md",
               "size":3405,
               "eTag":"6054b86291d4b94d4016462343bc1af5",
               "versionId":"NticBlEswOvUeEIwgvSM1KKZbsMQm1iH",
               "sequencer":"0060DC623F18331080"
            }
         }
      }
   ]
}
'''