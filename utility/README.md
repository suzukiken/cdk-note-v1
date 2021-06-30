```
python -m venv utility/env
source utility/env/bin/activate
pip install -r utility/requirements.txt
source utility/setenv.sh
python utility/es_create_index_and_mapping.py
python utility/es_search.py
```
