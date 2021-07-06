import boto3
import os
from datetime import date
import json
import urllib.parse
from github import Github
from os import listdir
from os.path import isfile, join
from shutil import copyfile

'''
このプログラムがやること

Webhookで呼び出され
呼び出したGithubのリポジトリのcontentディレクトリを捜査して
記事となりうるmdファイルをjsonに変換してS3におく

'''

GITHUB_ACCESS_TOKEN = os.environ.get('GITHUB_ACCESS_TOKEN')

g = Github(GITHUB_ACCESS_TOKEN)

GITHUB_PATH = "note/README.md"
GITHUB_BRANCH = "master"
GITHUB_OWNER = "suzukiken"


# ファイル

dirpath = '/home/ec2-user/environment/blog/content/aws/'

onlyfiles = []

for f in listdir(dirpath):
    print(f)
    if f.endswith('.md') and isfile(join(dirpath, f)):
        onlyfiles.append(f.replace('.md', ''))

print(onlyfiles)

# 今のgithubの内容を得る

github_repos = []

for repo in g.get_user().get_repos():
    if not repo.full_name.startswith(GITHUB_OWNER + '/') or repo.private:
        continue
    try:
        contents = repo.get_contents(GITHUB_PATH)
    except:
        continue
    else:
        github_repos.append(repo.name)

print(github_repos)

# 内容を比較して差異を抽出する

distpath = '/home/ec2-user/environment/blog/notes/'

for k in onlyfiles:
    if k in github_repos:
        pass
    else:
        copyfile(join(dirpath, k + '.md'), join(distpath, k + '.md'))