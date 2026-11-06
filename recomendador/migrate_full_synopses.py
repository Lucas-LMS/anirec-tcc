"""One-time migration of old manual-favorite snapshots (run with server stopped).

Imported AniList entries already keep original descriptions. Only old manual
favorites might have saved an 80-word public snapshot. Re-fetch these bounded
items; on any network error, do not save a partial migration.
"""
from engine import Engine

def main():
    engine=Engine()
    updated=[];changed=0
    for item in engine.profile.get('manual_favorites',[]):
        if item.get('synopsis_complete'):
            updated.append(item);continue
        if item.get('anilist_id'):
            replacement=engine.materialize(engine.client.media(item['anilist_id']))
        elif item['key'] in engine.base_media:
            replacement=engine.base_media[item['key']].copy()
        else:
            raise ValueError('Favorito sem fonte recuperável; migração não gravada.')
        updated.append(replacement);changed+=1
    if changed:
        engine.profile['manual_favorites']=updated
        engine.restore_profile_media();engine.save()
    print(f'Migração concluída: {changed} favoritos atualizados; histórico preservado.')

if __name__=='__main__':main()
