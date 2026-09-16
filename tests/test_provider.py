import io
import json
import os
import unittest
import urllib.error
from unittest.mock import patch
from codex_evolution.provider import redact, make_packet, interpret, capabilities, MAX_PACKET_CHARS
from codex_evolution.prompt_library import get_prompt, prompts

class ProviderTests(unittest.TestCase):
    def packet(self):
        return make_packet('instruction-audit',files=[{'path':'/private/AGENTS.md','text':'明确目标。\n每一步都必须先确认。'}])

    def response(self, report):
        return io.BytesIO(json.dumps({'status':'completed','output':[{'content':[{'type':'output_text','text':json.dumps(report)}]}]}).encode())

    def report(self):
        return {'summary':'可复核结论','findings':[{'title':'待审阅','evidence_ids':['F1-L2'],
            'interpretation':'此规则要求逐步确认。','action':'保留批准，仅提出改动建议。',
            'confidence':'medium','permission_expansion':True}], 'limitations':['需人工审阅。']}

    def test_redaction_common_secrets_not_claimed_complete(self):
        raw='sk-abcdefghijk123456789 ghp_abcdefghijkl123456 user@example.com /Users/alice/private/key.txt password=hunter2'
        safe=redact(raw)
        for secret in ['abcdefghijk123456789','abcdefghijkl123456','user@example.com','/Users/alice','hunter2']:
            self.assertNotIn(secret,safe)
        self.assertIn('REDACTED',safe)

    def test_packet_aliases_source_paths_and_cites_lines(self):
        packet=self.packet()
        self.assertEqual(packet['references'][1]['id'],'F1-L2')
        self.assertNotIn('/private',json.dumps(packet))
        self.assertEqual(packet['coverage']['reference_count'],2)
        self.assertIn('Best-effort',packet['privacy'])

    def test_long_packet_omissions_are_visible_and_valid_json(self):
        packet=make_packet('instruction-audit',files=[{'path':'AGENTS.md','text':'\n'.join(['x'*1100]*100)}])
        self.assertLessEqual(len(json.dumps(packet,ensure_ascii=False)),MAX_PACKET_CHARS)
        self.assertTrue(packet['coverage']['warnings'])
        self.assertEqual(packet['coverage']['reference_count'],len(packet['references']))

    def test_sample_limit_explicit(self):
        packet=make_packet('retrospective',samples=[{'text':'合成片段','role':'user'}]*100)
        self.assertEqual(len(packet['references']),36)
        self.assertTrue(any('NOT every conversation' in w for w in packet['coverage']['warnings']))

    def test_missing_keys_do_not_break_local_features(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertFalse(capabilities()['available'])
            self.assertEqual(len(prompts()),5)
            with self.assertRaisesRegex(ValueError,'Set OPENAI_API_KEY'): interpret(self.packet(),consent=True)

    def test_model_never_called_without_consent(self):
        with patch('urllib.request.urlopen') as request:
            with self.assertRaisesRegex(ValueError,'Explicit consent'): interpret(self.packet(),consent=False)
            request.assert_not_called()

    def test_responses_request_has_strict_schema_no_tools_and_no_storage(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'test-only-not-a-real-key','CODEX_EVOLUTION_MODEL':'test-model'}), patch('urllib.request.urlopen',return_value=self.response(self.report())) as request:
            result=interpret(self.packet(),consent=True)
            sent=json.loads(request.call_args.args[0].data)
            self.assertEqual(request.call_args.args[0].full_url,'https://api.openai.com/v1/responses')
            self.assertEqual(sent['model'],'test-model')
            self.assertFalse(sent['store'])
            self.assertNotIn('tools',sent)
            self.assertEqual(sent['text']['format']['type'],'json_schema')
            self.assertTrue(sent['text']['format']['strict'])
            self.assertEqual(result['changed_files'],[])

    def test_hallucinated_source_ids_removed_and_confidence_downgraded(self):
        report=self.report();report['findings'][0]['evidence_ids']=['F1-L2','NOT-REAL']
        with patch.dict(os.environ,{'OPENAI_API_KEY':'fake','CODEX_EVOLUTION_MODEL':'test-model'}), patch('urllib.request.urlopen',return_value=self.response(report)):
            result=interpret(self.packet(),consent=True)
        self.assertEqual(result['report']['findings'][0]['evidence_ids'],['F1-L2'])
        self.assertEqual(result['report']['findings'][0]['confidence'],'low')
        self.assertEqual(len(result['report']['limitations']),2)

    def test_provider_failures_are_sanitized(self):
        error=urllib.error.HTTPError('https://api.openai.com/v1/responses',401,'secret response',None,None)
        with patch.dict(os.environ,{'OPENAI_API_KEY':'fake','CODEX_EVOLUTION_MODEL':'test-model'}), patch('urllib.request.urlopen',side_effect=error):
            with self.assertRaises(ValueError) as caught: interpret(self.packet(),consent=True)
        self.assertIn('401',str(caught.exception))
        self.assertNotIn('secret response',str(caught.exception))

    def test_incomplete_and_malformed_reports_rejected(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'fake','CODEX_EVOLUTION_MODEL':'test-model'}):
            with patch('urllib.request.urlopen',return_value=io.BytesIO(b'{"status":"incomplete"}')):
                with self.assertRaisesRegex(ValueError,'incomplete'): interpret(self.packet(),consent=True)
            with patch('urllib.request.urlopen',return_value=self.response({'findings':[]})):
                with self.assertRaisesRegex(ValueError,'report shape'): interpret(self.packet(),consent=True)

    def test_user_requested_prompts_are_complete(self):
        audit=get_prompt('instruction-audit')
        self.assertIn('保留明确',audit)
        self.assertIn('权限',audit)
        self.assertIn('更改任何文件之前',audit)
        self.assertIn('SHA',get_prompt('anti-bloat'))
        self.assertIn('时间线',get_prompt('retrospective'))
        self.assertIn('Skill',get_prompt('workflow-to-skill'))
