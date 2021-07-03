from requests_aws4auth import AWS4Auth
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
import uuid
from datetime import datetime, timezone, timedelta
import time
import random
import os
from github import Github
import urllib.parse

region = "ap-northeast-1" 
service = "es"
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)

BUCKET_NAME = os.environ.get('BUCKET_NAME')
KEY_PREFIX = os.environ.get('KEY_PREFIX')
GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

g = Github(GITHUB_ACCESS_TOKEN)

GITHUB_PATH = "lib"
GITHUB_BRANCH = "master"
GITHUB_OWNER = "suzukiken"
GITHUB_URL_PREFIX = "https://github.com/"
GITHUB_URL_MIDDLE = "/blob/master/"

ENDPOINT = os.environ.get("ES_ENDPOINT")
INDEX = os.environ.get("ES_CODE_INDEX")
TYPE = "doc"

es = Elasticsearch(
    hosts=[{"host": ENDPOINT, "port": 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection
)

# 今のgithubの内容を得る

for repo in g.get_user().get_repos():
    if repo.full_name.startswith(GITHUB_OWNER + '/') and not repo.private:
        print(repo.name)
        try:
            contents = repo.get_contents(GITHUB_PATH)
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                else:
                    print(file_content)
                    try:
                        data = file_content.decoded_content.decode("utf-8")
                    except:
                        continue
                    else:
                        res = es.index(
                            index=INDEX, 
                            id=file_content.path, 
                            body={
                                'url': GITHUB_URL_PREFIX + repo.full_name + GITHUB_URL_MIDDLE + file_content.path,
                                'code': data
                            }, 
                            doc_type=TYPE
                        )
                        print(res)
        except:
            continue