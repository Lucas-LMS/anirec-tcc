-- Read-only examples. Database: /home/lucas/tcc-lab/recomendador-private/anirec.sqlite3
-- Choose an explicit dataset version from the first query for reproducibility.
SELECT version, created_at, quality_json FROM dataset_runs ORDER BY created_at DESC;

-- Works missing original synopsis (do not fabricate a text).
SELECT anilist_id,title FROM dataset_works
WHERE version = :version AND synopsis = '';

-- Genre coverage.
SELECT genre,COUNT(*) AS works FROM dataset_genres
WHERE version = :version GROUP BY genre ORDER BY works DESC;

-- Popular tags, keeping an explicit relevance threshold as an analysis choice.
SELECT tag_name,COUNT(*) AS works,AVG(rank) AS mean_rank FROM dataset_work_tags
WHERE version = :version AND rank >= 50
GROUP BY tag_name ORDER BY works DESC;

-- Candidate works with female protagonist and without registered male protagonist.
-- This does not prove absence of male protagonists when annotations are incomplete.
SELECT w.anilist_id,w.title FROM dataset_works w
WHERE w.version = :version
AND EXISTS (SELECT 1 FROM dataset_work_tags t WHERE t.version=w.version AND t.anilist_id=w.anilist_id AND t.tag_name='Female Protagonist')
AND NOT EXISTS (SELECT 1 FROM dataset_work_tags t WHERE t.version=w.version AND t.anilist_id=w.anilist_id AND t.tag_name='Male Protagonist');

-- Duplicate source mapping: AniList ID is canonical, never merge by MAL ID alone.
SELECT mal_id,COUNT(*) FROM dataset_works
WHERE version = :version AND mal_id IS NOT NULL GROUP BY mal_id HAVING COUNT(*)>1;

-- Audit vector dimensionality and storage: 100 float32 numbers = 400 bytes.
SELECT model,dimensions,dtype,COUNT(*) AS vectors,MIN(length(vector)),MAX(length(vector))
FROM dataset_vectors WHERE version = :version GROUP BY model,dimensions,dtype;
