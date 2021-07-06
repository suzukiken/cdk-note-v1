import boto3
import os
from datetime import date, datetime
import json
import urllib.parse
from github import Github
import re

'''
このプログラムがやること

Webhookで呼び出され
呼び出したGithubのリポジトリを捜査して
記事となりうるmdファイルをjsonに変換してS3におく

'''

BUCKET_NAME = os.environ.get('BUCKET_NAME')
KEY_PREFIX = os.environ.get('KEY_PREFIX')
GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

s3 = boto3.client('s3')
g = Github(GITHUB_ACCESS_TOKEN)

GITHUB_BRANCH = "master"
GITHUB_REPO = "suzukiken/notes"

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
        
        if GITHUB_REPO == full_name:
            
            # 今のS3の内容を得る
            
            s3_contents = {}
            
            list_response = s3.list_objects_v2(
                Bucket=BUCKET_NAME,
                Prefix=KEY_PREFIX
            )
            
            for content in list_response['Contents']:
                if not content['Key'].endswith('.json'):
                    continue
                get_response = s3.get_object(
                    Bucket=BUCKET_NAME,
                    Key=content['Key']
                )
                key = content['Key'].replace(KEY_PREFIX, '').replace('.json', '')
                s3_contents[key] = json.loads(get_response['Body'].read().decode('utf-8'))
        
            print(s3_contents.keys())
                
            # 今のgithubの内容を得る
            
            github_contents = {}
            
            repo = g.get_repo(GITHUB_REPO)
            
            try:
                contents = repo.get_contents('')
            except:
                pass
            else:
                print('contents: {}'.format(contents))
                while contents:
                    file_content = contents.pop(0)
                    if file_content.type == "dir":
                        contents.extend(repo.get_contents(file_content.path))
                    else:
                        print('file_content: {}'.format(file_content))
                        if not file_content.path.endswith('.md'):
                            continue
                        try:
                            text = file_content.decoded_content.decode("utf-8")
                        except:
                            continue
                        else:
                            article_name = file_content.path.replace('.md', '')
                            print('article_name: {}'.format(article_name))
                            title = category = tags = dte = upd = fco = ''
                            
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
                                
                            if title:
                                content = {
                                    'reponame': 'notes',
                                    'filename': article_name + '.json',
                                    'title': title,
                                    'category': category,
                                    'tags': tags,
                                    'date': dte,
                                    'update': upd,
                                    'content': fco,
                                }
                            
                                github_contents[article_name] = content
            
            print(github_contents.keys())
        
            # 内容を比較して差異を抽出する
            
            # TODO: github側でリポジトリの削除などで、S3にはデータがあるがgithubにはすでにデータがないという場合の対応
            
            diff = []
            
            for key in github_contents:
                if not key in s3_contents:
                    diff.append(key)
                else:
                    if s3_contents[key] != github_contents[key]:
                        diff.append(key)
                
            print(diff)
            
            # 差異をS3に反映する
            
            for key in diff:
                response = s3.put_object(
                    Bucket=BUCKET_NAME,
                    Key=KEY_PREFIX + key + '.json',
                    Body=json.dumps(github_contents[key], ensure_ascii=False, default=serialize)
                )
                
                print(response)