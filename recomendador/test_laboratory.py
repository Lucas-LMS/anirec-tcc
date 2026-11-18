"""Integrity checks for historical and full-catalog public model artifacts."""
import gzip
import hashlib
import json
import sqlite3
import unittest
from pathlib import Path

import numpy as np


class LaboratoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).parent / 'online'
        cls.catalog = json.loads((cls.root / 'catalog.json').read_text(encoding='utf-8'))

    def assert_model_matrices_valid(self, manifest, expected_keys):
        self.assertEqual(manifest['row_keys'], expected_keys)
        for model in manifest['models']:
            blob = (self.root / model['file']).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), model['sha256'])
            values = np.frombuffer(blob, dtype='<f4').reshape(model['rows'], model['dimensions'])
            self.assertTrue(np.isfinite(values).all())
            lengths = np.linalg.norm(values, axis=1)
            self.assertTrue(np.all((lengths == 0) | (np.abs(lengths - 1) < 1e-5)))
            self.assertEqual(int(sum(lengths == 0)), model['zero_documents'])

    def test_historical_models_match_historical_catalog(self):
        manifest = json.loads((self.root / 'lab/models-legacy-3413.json').read_text(encoding='utf-8'))
        records = self.catalog['records']
        self.assertEqual(hashlib.sha256((self.root / 'catalog.json').read_bytes()).hexdigest(), manifest['corpus_sha256'])
        self.assert_model_matrices_valid(manifest, [record['key'] for record in records])
        skipgram = next(model for model in manifest['models'] if model['id'] == 'skipgram')
        values = np.frombuffer((self.root / skipgram['file']).read_bytes(), dtype='<f4').reshape(skipgram['rows'], skipgram['dimensions'])
        np.testing.assert_allclose(values, np.asarray([record['vector'] for record in records]), rtol=1e-5, atol=1e-6)

    def test_full_catalog_models_match_comparison_snapshot(self):
        manifest = json.loads((self.root / 'lab/models.json').read_text(encoding='utf-8'))
        catalog_manifest = json.loads((self.root / 'lab/comparison-catalog-manifest.json').read_text(encoding='utf-8'))
        compressed = (self.root / catalog_manifest['file']).read_bytes()
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), catalog_manifest['compressed_sha256'])
        raw = gzip.decompress(compressed)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), catalog_manifest['sha256'])
        self.assertEqual(catalog_manifest['source_catalog_sha256'], manifest['corpus_sha256'])
        full_catalog = json.loads(raw.decode('utf-8'))
        self.assertEqual(len(full_catalog['records']), catalog_manifest['count'])
        self.assert_model_matrices_valid(manifest, [record['key'] for record in full_catalog['records']])

    def test_sqlite_matches_historical_public_snapshot_without_user_tables(self):
        catalog = json.loads((self.root / 'lab/dataset.json').read_text(encoding='utf-8'))
        with sqlite3.connect(self.root / 'lab/corpus.sqlite3') as db:
            self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM works').fetchone()[0], len(catalog['rows']))
            self.assertEqual(set(row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")), {'works', 'genres', 'tags', 'vectors', 'series_nodes', 'series_relations'})
            self.assertEqual(db.execute('SELECT COUNT(*) FROM vectors').fetchone()[0], 4 * len(catalog['rows']))
            self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
            self.assertGreater(db.execute('SELECT COUNT(*) FROM series_relations').fetchone()[0], 0)
            counts = db.execute('SELECT COUNT(average_score),COUNT(mean_score),COUNT(popularity),COUNT(community_favourites) FROM works').fetchone()
            self.assertEqual(counts, tuple(sum(row.get(key) is not None for row in catalog['rows']) for key in ['average_score', 'mean_score', 'popularity', 'community_favourites']))
            self.assertEqual(db.execute('SELECT COUNT(*) FROM works WHERE average_score<0 OR average_score>100 OR mean_score<0 OR mean_score>100 OR popularity<0 OR community_favourites<0').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
