import json
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from pathlib import Path
from codex_evolution.server import EvolutionServer
from codex_evolution.storage import Store

class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.store=Store(Path(cls.temp.name)/'app.sqlite')
        cls.server=EvolutionServer(('127.0.0.1',0),cls.store)
        cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.server.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown();cls.server.server_close();cls.thread.join(timeout=3);cls.temp.cleanup()

    def request(self,path,body=None,headers=None,token=True):
        h={'X-Evolution-Token':self.server.token} if token else {}
        if body is not None: h['Content-Type']='application/json'
        h.update(headers or {})
        data=json.dumps(body).encode() if body is not None else None
        req=urllib.request.Request(self.url+path,data=data,headers=h)
        try: response=urllib.request.urlopen(req,timeout=10)
        except urllib.error.HTTPError as e: response=e
        with response:
            text=response.read().decode('utf-8')
            value=json.loads(text) if response.headers.get('Content-Type','').startswith('application/json') else text
            return response.status,response.headers,value

    def setUp(self):
        self.store.clear()

    def test_real_http_assets_and_token_injection(self):
        status,headers,html=self.request('/',token=False)
        self.assertEqual(status,200)
        self.assertIn(self.server.token,html)
        self.assertNotIn('__SESSION_TOKEN__',html)
        self.assertIn("connect-src 'self'",headers['Content-Security-Policy'])
        self.assertEqual(self.request('/app.js',token=False)[0],200)
        self.assertEqual(self.request('/styles.css',token=False)[0],200)
        self.assertEqual(self.request('/../../etc/passwd',token=False)[0],404)

    def test_api_rejects_missing_token_wrong_origin_and_wrong_host(self):
        self.assertEqual(self.request('/api/status',token=False)[0],403)
        self.assertEqual(self.request('/api/status',headers={'Origin':'https://untrusted.example'})[0],403)
        self.assertEqual(self.request('/api/status',headers={'Host':'untrusted.example'})[0],403)
        self.assertEqual(self.request('/api/status',headers={'X-Evolution-Token':'wrong'})[0],403)
        self.assertEqual(self.request('/api/status')[0],200)

    def test_demo_live_isolation(self):
        self.assertEqual(self.request('/api/analysis?mode=demo')[2]['summary']['natural_messages'],3086)
        self.assertEqual(self.request('/api/analysis?mode=live')[2]['summary']['natural_messages'],0)
        self.assertEqual(self.request('/api/analysis?mode=other')[0],400)
        self.assertEqual(self.request('/api/analysis?start=2026-99')[0],400)

    def test_usage_http_import_export_and_conversation_separation(self):
        rows = [
            {'role': 'user', 'timestamp': '2026-01-01T10:00:00Z',
             'thread_id': 'private-thread', 'project': '/private/project', 'text': '验证这次修改'},
            {'type': 'usage', 'timestamp': '2026-01-01T10:00:02Z',
             'thread_id': 'private-thread', 'project': '/private/project', 'provider': 'openai',
             'model': 'test-model', 'response_id': 'private-response',
             'usage': {'input_tokens': 1000, 'cached_input_tokens': 600,
                       'output_tokens': 200, 'reasoning_output_tokens': 120, 'total_tokens': 1200}},
        ]
        body = {'files': [{'name': 'private-source.jsonl', 'text': '\n'.join(map(json.dumps, rows))}]}
        for _ in range(2):
            self.assertEqual(self.request('/api/import-upload', body)[0], 200)
        status, _, usage = self.request('/api/usage?mode=live')
        self.assertEqual(status, 200)
        self.assertEqual(usage['summary']['total_tokens'], 1200)
        self.assertEqual(usage['summary']['response_records'], 1)
        self.assertEqual(self.request('/api/analysis?mode=live')[2]['summary']['natural_messages'], 1)
        evidence = self.request('/api/evidence?mode=live&thread=private-thread')[2]
        self.assertEqual(len(evidence['items']), 1)
        self.assertEqual(evidence['items'][0]['text'], '验证这次修改')
        packet = self.request('/api/packet', {'kind': 'retrospective', 'mode': 'live'})[2]
        self.assertNotIn('private-response', json.dumps(packet))
        status, headers, exported = self.request('/api/usage-export?mode=live')
        self.assertEqual(status, 200)
        self.assertIn('attachment', headers['Content-Disposition'])
        for private in ['private-thread', '/private/project', 'private-response', 'private-source']:
            self.assertNotIn(private, json.dumps(exported))
        self.assertEqual(exported['summary']['total_tokens'], 1200)
        self.assertIsNone(self.request('/api/usage?mode=live&start=2026-02')[2]['summary']['total_tokens'])
        self.assertEqual(self.request('/api/usage?start=2026-99')[0], 400)
        self.assertEqual(self.request('/api/usage', token=False)[0], 403)
        self.assertEqual(self.request('/api/usage-export', token=False)[0], 403)

    def test_usage_demo_is_synthetic_and_assets_are_served(self):
        usage = self.request('/api/usage?mode=demo')[2]
        self.assertGreater(usage['summary']['total_tokens'], 0)
        self.assertIsNone(self.request('/api/usage?mode=live')[2]['summary']['total_tokens'])
        self.assertEqual(self.request('/api/analysis?mode=demo')[2]['summary']['natural_messages'], 3086)
        self.assertEqual(self.request('/api/analysis?mode=demo')[2]['summary']['threads'], 132)
        for asset in ['usage-ui.js', 'usage.css', 'improve-ui.js', 'improve.css']:
            self.assertEqual(self.request('/' + asset, token=False)[0], 200)

    def test_upload_reimport_and_clear_are_real_storage_operations(self):
        text=json.dumps({'role':'user','thread_id':'upload-thread','timestamp':'2026-01-01T00:00:00Z','text':'继续测试'})
        body={'files':[{'name':'fixture.jsonl','text':text}]}
        for _ in range(2): self.assertEqual(self.request('/api/import-upload',body)[0],200)
        self.assertEqual(self.request('/api/analysis?mode=live')[2]['summary']['natural_messages'],1)
        result=self.request('/api/evidence?mode=live&word=continue')[2]
        self.assertEqual(result['items'][0]['text'],'继续测试')
        self.assertEqual(self.request('/api/clear',{'confirmation':'wrong'})[0],400)
        self.assertEqual(self.request('/api/clear',{'confirmation':'DELETE LOCAL IMPORTS'})[0],200)
        self.assertEqual(self.request('/api/analysis?mode=live')[2]['summary']['natural_messages'],0)
        self.assertEqual(self.request('/api/analysis?mode=demo')[2]['summary']['natural_messages'],3086)

    def test_upload_rejects_credentials_absolute_and_traversal_names(self):
        for name in ['auth.json','../secret.jsonl','/etc/secret.jsonl','C:\\secret.jsonl','file.txt']:
            with self.subTest(name=name):
                self.assertEqual(self.request('/api/import-upload',{'files':[{'name':name,'text':'[]'}]})[0],400)

    def test_import_path_keeps_original_intact(self):
        source=Path(self.temp.name)/'original-history.jsonl'
        source.write_text(json.dumps({'session_id':'s','ts':1767225600,'text':'请继续'}))
        before=source.read_bytes()
        self.assertEqual(self.request('/api/import',{'path':str(source)})[0],200)
        self.assertEqual(source.read_bytes(),before)
        self.assertEqual(self.request('/api/analysis?mode=live')[2]['summary']['natural_messages'],1)

    def test_audit_and_model_packet_routes(self):
        files=[{'path':'AGENTS.md','text':'每一步都必须先向用户确认。'}]
        result=self.request('/api/audit',{'kind':'instructions','files':files})
        self.assertEqual(result[0],200)
        self.assertEqual(result[2]['summary']['findings'],1)
        packet=self.request('/api/packet',{'kind':'instruction-audit','files':files})[2]
        self.assertEqual(packet['packet']['references'][0]['id'],'F1-L1')
        self.assertIn('保留明确',packet['prompt'])
        self.assertEqual(self.request('/api/model',{'packet':packet['packet'],'consent':False})[0],400)

    def test_reports_are_real_downloads_and_aggregate_only(self):
        for format_,fragment in [('html','<!doctype html>'),('md','## 数据范围'),('csv','month')]:
            with self.subTest(format=format_):
                status,headers,value=self.request('/api/report?mode=demo&format='+format_)
                self.assertEqual(status,200)
                self.assertIn('attachment',headers['Content-Disposition'])
                self.assertIn(fragment,value)
        report=self.request('/api/report?mode=demo&format=json')[2]
        self.assertNotIn('projects',report)
        self.assertNotIn('filters',report)
        self.assertEqual(self.request('/api/report?format=exe')[0],400)

    def test_public_bind_is_not_supported(self):
        with self.assertRaises(ValueError): EvolutionServer(('0.0.0.0',0),self.store)
