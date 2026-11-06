"""Annotate recovery without altering any response or inventing missing time."""
import json
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];TARGET=BASE/'resultados/benchmark-v1/qwen'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def lines(p):return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines()]
records=lines(TARGET/'requests.jsonl');original=lines(TARGET/'requests-primeiras-185.jsonl')
assert len(records)==200 and len(original)==185 and records[:185]==original
meta=load(TARGET/'resultado.json');event=load(TARGET/'interruption.json')
assert records[185]['id']==event['affected_id']
meta.update(resume_segment_wall_seconds=meta.get('resume_segment_wall_seconds',meta['total_stage_wall_seconds']),total_stage_wall_seconds=None,execution_segments=2,resumed_existing_records=185,interruption=event,
    load_seconds_scope='Second server startup only; original load measurement not preserved in final metadata.',
    total_stage_note='Original first-segment total was not captured after exception. Do not substitute resume duration or nominal timeout for a measured full total.',
    completed_response_timing_note='All 200 completed-response latencies retained; prior timeout attempt excluded; first resumed query has no fresh synthetic warmup.',
    known_successful_test_tokens=sum(x.get('usage',{}).get('total_tokens',0) for x in records),
    successful_test_calls=200,failed_test_attempts=1,successful_warmup_calls=1,
    first_attempt_response_availability=199/200,
    peak_rss_note='Use the maximum of the first-segment GNU time RSS and the resumed server VmHWM; do not sum process peaks.')
temp=TARGET/'resultado-recovery.tmp';temp.write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(TARGET/'resultado.json')
print('Metadados corrigidos: 200 respostas; prefixo de 185 preservado; tempo total não inventado.')
