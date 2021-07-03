from requests_aws4auth import AWS4Auth
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import uuid
from datetime import datetime, timezone, timedelta
import time
import random
import os

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

body = {
    "from": 0,
    "size": 1000,
    "query": {
        "match": {
            "code": {
                "query": "CdkappsyncLambdaStack"
            }
        }
    },
    "highlight": {
        "fields": {
            "url": {},
            "code": {},
        }
    }
}

res = es.search(
    index=INDEX,
    doc_type=TYPE,
    body=body
)

for hit in res["hits"]["hits"]:
    print("{} {}".format(hit["_source"]["url"], hit["highlight"]["code"]))
