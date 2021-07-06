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

    for record in event['Records']:
        if record['EventSource'] != 'aws:sns':
            continue
        
        message = json.loads(record['Sns']['Message'])
        
        for record_in_message in message['Records']:
            if record_in_message['s3']['bucket']['name'] != BUCKET_NAME:
                continue
            
            eventname = record_in_message['eventName'].split(':')[0]
            
            if eventname == 'ObjectCreated':
                pass
            elif eventname == 'ObjectRemoved':
                continue
            else:
                continue
            
            get_response = s3.get_object(
                Bucket=record_in_message['s3']['bucket']['name'],
                Key=record_in_message['s3']['object']['key'],
            )
            
            article = json.loads(get_response['Body'].read().decode('utf-8'))
            
            if 'reponame' in article:
                del article['reponame']
            
            es_put_article(article)

'''
{
   "Records":[
      {
         "EventSource":"aws:sns",
         "EventVersion":"1.0",
         "EventSubscriptionArn":"arn:aws:sns:ap-northeast-1:656169322665:CdkNoteStrageStack-TopicBFC7AF6E-AOCFS613C2CF:8af863bc-70db-4bbd-8b78-34f4ece3c315",
         "Sns":{
            "Type":"Notification",
            "MessageId":"77d078b2-0213-5158-b33b-21e50310682f",
            "TopicArn":"arn:aws:sns:ap-northeast-1:656169322665:CdkNoteStrageStack-TopicBFC7AF6E-AOCFS613C2CF",
            "Subject":"Amazon S3 Notification",
            "Message":"{\"Records\":[{\"eventVersion\":\"2.1\",\"eventSource\":\"aws:s3\",\"awsRegion\":\"ap-northeast-1\",\"eventTime\":\"2021-06-30T23:31:10.344Z\",\"eventName\":\"ObjectRemoved:DeleteMarkerCreated\",\"userIdentity\":{\"principalId\":\"AWS:AIDAIRGQRKVJ6LFTAV2U2\"},\"requestParameters\":{\"sourceIPAddress\":\"124.84.26.167\"},\"responseElements\":{\"x-amz-request-id\":\"MCWT21M8ZYQDX2SC\",\"x-amz-id-2\":\"3CHzogkHzCfXNkZxlMDRaJWVQVZV7TGne5wnT3O21Q0zYFcG3r8UlJCqiYm3gYhNJmOI2BprlIX4N3TFXcwaraHopALQ0gEJ\"},\"s3\":{\"s3SchemaVersion\":\"1.0\",\"configurationId\":\"ZWUzOTg0N2ItMmYyNy00ZmE1LTg2MGMtMjgyMzUyMWFkYWRm\",\"bucket\":{\"name\":\"cdknotestragestack-bucket83908e77-15iapvi94z1g2\",\"ownerIdentity\":{\"principalId\":\"A3IE8ALDKUHMWU\"},\"arn\":\"arn:aws:s3:::cdknotestragestack-bucket83908e77-15iapvi94z1g2\"},\"object\":{\"key\":\"articles/cdk-fargate.md\",\"eTag\":\"d41d8cd98f00b204e9800998ecf8427e\",\"versionId\":\"8rGy4fFtHEbSjtj91trn6ky7yAU5_ALR\",\"sequencer\":\"0060DCFEC27EF6D23F\"}}}]}",
            "Timestamp":"2021-06-30T23:31:15.831Z",
            "SignatureVersion":"1",
            "Signature":"UUA0N8OERQXtMo+30iBOpFSuoNQDCc2K5emgtW5/rfFuH1dvIeHwZM/hOmT9ynzHyR4Qsb/VXkSIC8zL/pmkmZORi02Lg6aALE1WNIeqti01Cmahxz1I1H4ikhhVHJ1r7zArzOqjJAXsar+O7y65rDltctO2thlYdwgde0QixXABTeEoI+yZiyYBCghFq84NK1QwAeGaryjlwLQYNHhL0WfCgzzPV9MnzbnG9VsrX8YS1roWtpY4sQtRIB2vi5HHhjz1UOxlo6wzN5Xd/n13P5cvvy7plldKDYKU16JLm0gicQrSwN9Xt8TFM2sRyYiIGD19ydvkwfvggyLiiowAXA==",
            "SigningCertUrl":"https://sns.ap-northeast-1.amazonaws.com/SimpleNotificationService-010a507c1833636cd94bdb98bd93083a.pem",
            "UnsubscribeUrl":"https://sns.ap-northeast-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:ap-northeast-1:656169322665:CdkNoteStrageStack-TopicBFC7AF6E-AOCFS613C2CF:8af863bc-70db-4bbd-8b78-34f4ece3c315",
            "MessageAttributes":{
               
            }
         }
      }
   ]
}
'''