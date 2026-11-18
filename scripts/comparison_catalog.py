"""Create the small, vector-free catalog payload used by the static model worker."""
from __future__ import annotations
import gzip
import hashlib
import json
from pathlib import Path

FIELDS = ('key', 'title', 'romaji', 'anilist_id', 'text', 'genres', 'tags', 'status',
          'average_score', 'mean_score', 'is_adult')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_comparison_catalog(online: Path) -> dict:
    build = json.loads((online / 'build-manifest.json').read_text(encoding='utf-8'))
    packed = (online / build['catalog_file']).read_bytes()
    raw = gzip.decompress(packed) if build['catalog_file'].endswith('.gz') else packed
    if sha(raw) != build['sha256']:
        raise ValueError('Hash do catálogo principal inválido.')
    catalog = json.loads(raw)
    compact = {key: catalog[key] for key in ('encoding_id', 'params', 'topic_idf', 'source')}
    compact['records'] = [{key: row[key] for key in FIELDS} for row in catalog['records']]
    compact_raw = json.dumps(compact, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
    output_name = 'comparison-catalog.json.gz'
    output = online / 'lab' / output_name
    output.parent.mkdir(parents=True, exist_ok=True)
    compressed = gzip.compress(compact_raw, compresslevel=9, mtime=0)
    output.write_bytes(compressed)
    result = {
        'file': 'lab/' + output_name, 'count': len(compact['records']),
        'sha256': sha(compact_raw), 'compressed_sha256': sha(compressed),
        'compressed_bytes': len(compressed), 'source_catalog_sha256': build['sha256'],
        'purpose': 'Metadata and synopsis payload for the full-catalog static model comparator; per-model document vectors are loaded separately.',
    }
    (online / 'lab' / 'comparison-catalog-manifest.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main() -> None:
    online = Path(__file__).resolve().parents[1] / 'recomendador' / 'online'
    print(json.dumps(build_comparison_catalog(online), ensure_ascii=False))


if __name__ == '__main__':
    main()
