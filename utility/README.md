```
python -m venv utility/env
source utility/env/bin/activate
pip install -r utility/requirements.txt
source utility/setenv.sh
python utility/es_create_index_and_mapping_article.py
python utility/es_search_article.py
python utility/es_create_index_and_mapping_code.py
python utility/es_delete_index_code.py
python utility/es_search_code.py
```
