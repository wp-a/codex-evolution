"""Small public-format, synthetic fixtures. Never copy personal histories into tests."""
from codex_evolution.ingest import Message, timestamp, natural_user

def row(text='继续', *, day='2026-01-01T12:00:00+00:00', thread='t1',
        source='fixture.jsonl', line=1, role='user', channel='normalized', project='/demo/project', tool=''):
    return Message(source, line, thread, timestamp(day), role, text, channel,
                   project, tool, role == 'user' and natural_user(text)).record()
