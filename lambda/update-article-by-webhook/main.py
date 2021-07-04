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

tiexp = 'title = "(.+?)"'
tgexp = 'tags = \[(.+?)\]'
dtexp = 'date = "(.+?)"'
upexp = 'update = "(.+?)"'
ctexp = 'category = "(.+?)"'
coexp = '\n[+]{3}\n(.*)'

def serialize(anyobj):
    if isinstance(anyobj, (datetime, date)):
        return anyobj.isoformat()
    raise TypeError ('not date')

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
        
        github_contents = {}
        
        try:
            contents = repo.get_contents(GITHUB_PATH)
        except:
            pass
        else:
            #print('contents: {}'.format(contents))
            text = contents.decoded_content.decode("utf-8")
            
            try:
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
                
                github_contents = {
                    'reponame': repo.name,
                    'filename': repo.name + '.json',
                    'title': title,
                    'category': category,
                    'tags': tags,
                    'date': dte,
                    'update': upd,
                    'content': fco,
                }
                
            except:
                continue

        # 今のS3の内容を得る
        
        s3_contents = ''
        
        try:
            get_response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=KEY_PREFIX + repo.name + '.json',
            )
            s3_contents = json.loads(get_response['Body'].read().decode('utf-8'))
        except:
            pass
        
        #print(s3_contents)
        
        # 差異をS3に反映する
        
        if not s3_contents == github_contents:
            put_response = s3.put_object(
                Bucket=BUCKET_NAME,
                Key=KEY_PREFIX + repo.name + '.json',
                Body=json.dumps(github_contents, ensure_ascii=False, default=serialize)
            )
            
            print(put_response)
        
