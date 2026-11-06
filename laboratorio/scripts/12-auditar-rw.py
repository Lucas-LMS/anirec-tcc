"""Auditoria propria da copia RW AWS e corroboracao por repositorio academico.

Confere pares/notas medias, nao a identidade binaria com o servidor Stanford.
Nao executa o notebook AWS nem instala codigo do repositorio de corroboracao.
"""
import collections
import decimal
import hashlib
import json
import pathlib
import sys
import zipfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def records(data):
    output = []
    for line in data.decode('utf-8').splitlines():
        if not line.strip():
            continue
        fields = line.split()
        assert 3 <= len(fields) <= 13, fields
        score = decimal.Decimal(fields[2])
        assert score.is_finite() and 0 <= score <= 10
        output.append((fields[0], fields[1], score))
    return output


def main():
    archive_path, academic_path, notebook_path, report_path, destination = map(pathlib.Path, sys.argv[1:])
    archive = archive_path.read_bytes()
    academic = academic_path.read_bytes()
    blob = hashlib.sha1(b'blob '+str(len(academic)).encode()+b'\0'+academic).hexdigest()
    assert blob == '35498f2fb426bc8e663cb426ed597455b3ecd8cf', 'Copia academica mudou; auditar nova revisao'
    notebook = notebook_path.read_text(encoding='utf-8')
    assert 'sagemaker-example-files-prod-' in notebook and 'datasets/text/stanford_rare_words/rw.zip' in notebook
    with zipfile.ZipFile(archive_path) as source:
        assert source.testzip() is None
        original = source.read('rw/rw.txt')
        readme = source.read('rw/README.txt')
    assert b'Stanford Rare Word' in readme and b'2034' in readme
    aws_rows, academic_rows = records(original), records(academic)
    same = collections.Counter(aws_rows) == collections.Counter(academic_rows)
    result = {
        'original_url': 'https://nlp.stanford.edu/~lmthang/morphoNLM/rw.zip',
        'download_url': 'https://sagemaker-example-files-prod-us-east-1.s3.amazonaws.com/datasets/text/stanford_rare_words/rw.zip',
        'aws_source_notebook': 'https://github.com/aws/amazon-sagemaker-examples/blob/4883224d0032906f1a2bafd4887544ff5ddae606/introduction_to_amazon_algorithms/blazingtext_word2vec_subwords_text8/blazingtext_word2vec_subwords_text8.ipynb',
        'archive_sha256': digest(archive), 'rw_txt_sha256': digest(original),
        'archive_bytes': len(archive), 'rw_txt_bytes': len(original),
        'corroboration_url': 'https://github.com/mfaruqui/eval-word-vectors/blob/master/data/word-sim/EN-RW-STANFORD.txt',
        'corroboration_git_blob_sha1': blob, 'corroboration_sha256': digest(academic),
        'aws_pairs': len(aws_rows), 'corroboration_pairs': len(academic_rows),
        'all_word_pairs_and_mean_scores_match': same,
        'row_order_matches': aws_rows == academic_rows,
        'compared_to_stanford_published_checksum': False,
        'stanford_byte_identity_proven': False,
        'note': 'Copia AWS com pares/notas medias corroborados; origem alternativa explicita. Sem checksum Stanford disponivel.',
    }
    report_path.write_text(json.dumps(result, indent=2), encoding='utf-8')
    assert len(aws_rows) == len(academic_rows) == 2034 and same, 'Divergencia: nao instalar dados'
    destination.mkdir(parents=True, exist_ok=True)
    for filename, content in [('rw.txt', original), ('README.txt', readme)]:
        target = destination/filename
        if target.exists():
            assert target.read_bytes() == content, f'Arquivo existente diferente: {target}'
        else:
            target.write_bytes(content)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
