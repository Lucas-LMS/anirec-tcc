"""Verify the explicitly supplied public username; do not import the list yet."""
import json
from pathlib import Path
from anilist_client import AniListClient
user=AniListClient().user('banthisworld')
print(json.dumps(dict(found=bool(user),id=user.get('id') if user else None,name=user.get('name') if user else None)))
