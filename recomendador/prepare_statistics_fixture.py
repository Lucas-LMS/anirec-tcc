import json
from pathlib import Path
from test_user_statistics import RECORDS,ENTRIES
from user_statistics import compute_statistics
target=Path(__file__).resolve().parents[1]/'tmp/statistics-fixtures.json';target.parent.mkdir(exist_ok=True);target.write_text(json.dumps([{'records':RECORDS,'entries':ENTRIES,'scope':scope,'expected':compute_statistics(RECORDS,ENTRIES,scope)} for scope in ['ALL','STARTED','COMPLETED','PLANNING']]),encoding='utf-8');print('Statistics fixtures: 4 scopes')
