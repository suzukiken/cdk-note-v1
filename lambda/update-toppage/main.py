import boto3
import os
import re
from datetime import date
import json

'''
このプログラムがやること

S3のコンテンツが更新されると呼び出される
そのコンテンツはHugoのFront Matterがついたmarkdownとなっている
そこからタイトルやタグを取り出して
まだ決めていないが何らかのルールに沿ってそれを必要なところに並べてトップページを作る。
そのルールはいずれはコンフィグファイルのようなものを参照しておすすめコンテンツを左コラムに配置するとか、
カテゴリで分けて表示するとか、最初のタグで分けて表示するとかしたいと思っている。
しかしそんなコンフィグファイルはまだ作っていないので、とりあえず今のところはコンテンツの更新日順に降順で並べるという程度にしておく。
'''

BUCKET_NAME = os.environ.get('BUCKET_NAME')

client = boto3.client('s3')

tiexp = 'title = "(.+?)"'
tgexp = 'tags = \[(.+?)\]'
dtexp = 'date = "(.+?)"'
coexp = '\n[+]{3}\n(.*)'

SUMMARY_KEY = 'summary-title.json'
TAG_KEY = 'summary-tag.json'

def lambda_handler(event, context):
    print(event)
    '''
    
    do = False
    
    for record in event['Records']:
        
        if record['eventSource'] != 'aws:s3':
            continue
        
        if record['s3']['bucket']['name'] != BUCKET_NAME:
            continue
        
        do = True
    
    if not do:
        return
    
    list_response = client.list_objects_v2(
        Bucket=BUCKET_NAME
    )
    
    articles = []
    
    for content in list_response['Contents']:
        
        filename = content['Key']
        
        if not filename.endswith('.md'):
            continue
        
        get_response = client.get_object(
            Bucket=BUCKET_NAME,
            Key=filename,
        )

        try:
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
            
            mat = re.search(coexp, text, flags=re.DOTALL)
            if mat:
                fco = mat.group(1)
            
            articles.append({
                "filename": filename,
                "title": title,
                "tags": tags,
                "date": dte,
                "content": fco,
            })
        except:
            continue
    
    summary = []
    
    for article in articles:
        summary.append({
            'title': article['title'],
            'date': article['date'].isoformat(),
            'tags': article['tags'],
            'filename': article['filename']
        })
    
        
    put_response = client.put_object(
        Bucket=BUCKET_NAME,
        Key=SUMMARY_KEY,
        Body=json.dumps(summary, ensure_ascii=False)
    )
    
    print(put_response)
    
    category = {}
    
    for article in articles:
        tag = article['tags'][0]
        if not tag in category:
            category[tag] = []
        category[tag].append({
            'title': article['title'],
            'date': article['date'].isoformat(),
            'tags': article['tags'],
            'filename': article['filename']
        })
    
    put_response = client.put_object(
        Bucket=BUCKET_NAME,
        Key=TAG_KEY,
        Body=json.dumps(category, ensure_ascii=False)
    )
    '''