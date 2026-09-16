import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from codex_evolution.ingest import parse_text, timestamp, natural_user, canonical_messages, discover, import_path
from codex_evolution.storage import Store
from tests.helpers import row

class IngestTests(unittest.TestCase):
    def test_timestamp_seconds_milliseconds_and_iso(self):
        self.assertEqual(timestamp(1767225600), timestamp(1767225600000))
        self.assertEqual(timestamp('2026-01-01T08:00:00+08:00'), timestamp('2026-01-01T00:00:00Z'))
        for value in [None, True, 'no-date', float('nan'), '2200-01-01']:
            self.assertIsNone(timestamp(value))

    def test_codex_event_priority_over_mirrored_response(self):
        objects = [
            {'type':'session_meta','payload':{'id':'session-a','cwd':'/demo/app'}},
            {'type':'event_msg','timestamp':'2026-01-01T00:00:00Z', 'payload':{'type':'user_message','message':'请继续'}},
            {'type':'response_item','timestamp':'2026-01-01T00:00:00Z', 'payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'请继续'}]}},
            {'type':'response_item','timestamp':'2026-01-01T00:00:01Z', 'payload':{'type':'function_call','name':'exec_command','arguments':'{"cmd":"echo synthetic"}'}},
            {'type':'event_msg','timestamp':'2026-01-01T00:00:02Z','payload':{'type':'agent_message','message':'合成回复'}},
        ]
        result = parse_text('\n'.join(json.dumps(o) for o in objects), 'rollout.jsonl')
        self.assertEqual([m.role for m in result.messages], ['user','tool','assistant'])
        self.assertEqual(result.messages[0].thread_id, 'session-a')
        self.assertEqual(result.messages[0].project, '/demo/app')
        self.assertEqual(result.messages[1].tool, 'exec_command')
        self.assertEqual(result.diagnostics['mirrored_user_records'], 1)
        self.assertEqual(result.messages[0].line, 2)

    def test_response_only_adapter(self):
        obj = {'type':'response_item','timestamp':'2026-01-01T00:00:00Z','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'看看实现'}]}}
        parsed=parse_text(json.dumps(obj), 'fallback.jsonl')
        self.assertEqual(parsed.messages[0].text,'看看实现')
        self.assertEqual(parsed.messages[0].channel,'response')

    def test_history_adapter(self):
        parsed=parse_text(json.dumps({'session_id':'s','ts':1767225600,'text':'继续'}), 'history.jsonl')
        self.assertEqual(parsed.messages[0].thread_id,'s')
        self.assertEqual(parsed.messages[0].channel,'history')

    def test_normalized_array_and_bad_lines(self):
        records=[{'timestamp':'2026-01-01T00:00:00Z','role':'user','text':'测试','thread_id':'one'}]
        parsed=parse_text(json.dumps({'messages':records}), 'export.json', json_document=True)
        self.assertEqual(len(parsed.messages),1)
        broken=parse_text('not json\n'+json.dumps(records[0])+'\n'+json.dumps({'type':'new_format'}), 'mixed.jsonl')
        self.assertEqual(broken.diagnostics['invalid_json'],1)
        self.assertEqual(broken.diagnostics['unknown_events'],1)
        self.assertEqual(broken.messages[0].line,2)

    def test_natural_message_filter(self):
        for text in ['', '  ', '<environment_context>test', '# AGENTS.md instructions for /repo', '<INSTRUCTIONS>private']:
            self.assertFalse(natural_user(text))
        self.assertTrue(natural_user('请审阅 AGENTS.md 文件'))
        self.assertTrue(natural_user('继续'))

    def test_invalid_time_does_not_become_today(self):
        parsed=parse_text(json.dumps({'role':'user','text':'继续','timestamp':'invalid'}), 'invalid.jsonl')
        self.assertEqual(len(parsed.messages),0)
        self.assertEqual(parsed.diagnostics['invalid_timestamps'],1)

    def test_cross_stream_one_to_one_mirrors(self):
        rows=[row(line=i,channel='event',source='rollout.jsonl') for i in (1,2)]
        rows += [row(line=i,channel='history',source='history.jsonl') for i in (1,2)]
        canonical, duplicates=canonical_messages(rows)
        self.assertEqual(len(canonical),2)
        self.assertEqual(duplicates,2)
        self.assertEqual([r['channel'] for r in canonical],['event','event'])

    def test_same_stream_repeated_continue_and_other_threads_survive(self):
        rows=[row(line=1),row(line=2),row(thread='different',source='other.jsonl')]
        canonical,duplicates=canonical_messages(rows)
        self.assertEqual(len(canonical),3)
        self.assertEqual(duplicates,0)

    def test_mirror_match_has_time_window_and_does_not_mutate_input(self):
        a=row(channel='event',project='unassigned')
        b=row(channel='history',source='history.jsonl',project='/demo/real')
        c=row(channel='history',source='history.jsonl',line=2,day='2026-01-01T12:00:10Z')
        canonical,duplicates=canonical_messages([a,b,c])
        self.assertEqual(len(canonical),2)
        self.assertEqual(duplicates,1)
        self.assertEqual(a['project'],'unassigned')
        self.assertEqual(canonical[0]['project'],'/demo/real')

    def test_discovery_whitelist_and_credentials_excluded(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);(root/'sessions').mkdir();(root/'logs').mkdir()
            for path in [root/'history.jsonl', root/'sessions'/'r.jsonl', root/'logs'/'private.jsonl', root/'auth.json']:
                path.write_text('{}',encoding='utf-8')
            paths=discover(root)
            self.assertEqual({p.name for p in paths},{'history.jsonl','r.jsonl'})
            with self.assertRaises(ValueError): discover(root/'auth.json')
            with self.assertRaises(ValueError): parse_text('{}','auth.json',json_document=True)

    def test_metadata_sqlite_is_read_only_enrichment(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'history.jsonl').write_text(json.dumps({'session_id':'s','ts':1767225600,'text':'继续'}))
            database=root/'state_5.sqlite'
            with sqlite3.connect(database) as db:
                db.execute('CREATE TABLE threads(id TEXT,cwd TEXT)')
                db.execute('INSERT INTO threads VALUES (?,?)',('s','/demo/enriched'))
            db.close()
            before=database.read_bytes()
            result=import_path(root)
            self.assertEqual(result.messages[0].project,'/demo/enriched')
            self.assertEqual(before,database.read_bytes())
            self.assertTrue(any('Local projection' in w for w in result.diagnostics['warnings']))

    def test_store_reimport_is_idempotent_and_replaces_source_snapshot(self):
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder)/'app.sqlite')
            def text(n):
                return '\n'.join(json.dumps({'role':'user','timestamp':'2026-01-01T00:00:00Z','text':'继续'}) for _ in range(n))
            result=parse_text(text(2),'input.jsonl')
            store.ingest(result);store.ingest(result)
            self.assertEqual(len(store.messages()),2)
            store.ingest(parse_text(text(1),'input.jsonl'))
            self.assertEqual(len(store.messages()),1)
            store.clear()
            self.assertEqual(store.messages(),[])
            self.assertIsNone(store.diagnostics()['last_import'])
