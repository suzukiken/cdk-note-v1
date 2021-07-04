```
python -m venv test/env
source test/env/bin/activate
pip install -r lambda/update-article/requirements.txt
pip install python-lambda-local
pip install boto3
touch test/event.json
touch test/setenv.sh
echo "{}" > test/event.json
source test/setenv.sh
python-lambda-local -t 10 -f lambda_handler lambda/update-article/main.py test/event.json
python-lambda-local -t 10 -f lambda_handler lambda/update-index/main.py test/event.json
python-lambda-local -t 10 -f lambda_handler lambda/update-toppage/main.py test/event.json
python-lambda-local -t 10 -f lambda_handler lambda/update-article-by-webhook/main.py test/event-sns-from-webhook.json
python-lambda-local -t 10 -f lambda_handler lambda/called-by-webhook/main.py test/event-webhook.json
python-lambda-local -t 10 -f lambda_handler lambda/update-code-by-webhook/main.py test/event-sns-from-webhook.json
python-lambda-local -t 100 -f lambda_handler lambda/update-article-periodically/main.py test/event.json
```