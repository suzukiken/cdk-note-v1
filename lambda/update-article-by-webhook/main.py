import boto3
import os
import re
from datetime import date
import json
from github import Github
import urllib.parse

'''
このプログラムがやること

Githubのpushをwebhookとして受ける

そのリポジトリの中にあるnote/README.mdをS3のバケットにコピーする。
（すでに同じ内容がある場合は上書きしない。
上書きすると別のLambdaに通知されてElasticSearchのインデックス更新が無駄に行われてしまうため。）

'''

BUCKET_NAME = os.environ.get('BUCKET_NAME')
KEY_PREFIX = os.environ.get('KEY_PREFIX')
GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

s3 = boto3.client('s3')
g = Github(GITHUB_ACCESS_TOKEN)

GITHUB_PATH = "note/README.md"
GITHUB_BRANCH = "master"
GITHUB_OWNER = "suzukiken"

def lambda_handler(event, context):
    print(event)
    
    for record in event['Records']:
        if record['EventSource'] != 'aws:sns':
            continue
        
        message = json.loads(record['Sns']['Message'])
        repository = message['repository']
        full_name = repository['full_name']
        repo = g.get_repo(full_name)
        
        # githubの内容を得る
        
        if repo.private:
            return
        
        github_contents = ''
        
        try:
            contents = repo.get_contents(GITHUB_PATH)
        except:
            pass
        else:
            #print('contents: {}'.format(contents))
            github_contents = contents.decoded_content.decode("utf-8")

        # 今のS3の内容を得る
        
        s3_contents = ''
        
        try:
            get_response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=KEY_PREFIX + repo.name + '.md',
            )
            s3_contents = get_response['Body'].read().decode('utf-8')
        except:
            pass
        
        #print(s3_contents)
        
        # 差異をS3に反映する
        
        if not s3_contents == github_contents:
            put_response = s3.put_object(
                Bucket=BUCKET_NAME,
                Key=KEY_PREFIX + repo.name + '.md',
                Body=github_contents
            )
            
            print(put_response)
        
