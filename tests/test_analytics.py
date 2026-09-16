import json
import unittest
from codex_evolution.analytics import analyze, evidence, mine_workflows, month_keys
from codex_evolution.demo import demo_messages
from codex_evolution.rules import word_hits
from codex_evolution.reports import public_analysis, report_markdown, report_html, report_csv
from tests.helpers import row

class AnalyticsTests(unittest.TestCase):
    def test_message_hit_not_token_frequency_and_overlapping_groups(self):
        data=analyze([row('继续继续，请帮我测试'),row('完成',line=2)])
        words={w['key']:w for w in data['words']}
        self.assertEqual(words['continue']['count'],1)
        self.assertEqual(words['continue']['rate'],50)
        self.assertEqual(words['help']['rate'],50)
        self.assertEqual(words['verify']['rate'],50)
        self.assertEqual(data['summary']['threads'],1)
        self.assertEqual(data['monthly'][0]['threads'],1)

    def test_system_injections_and_assistant_are_not_natural_denominator(self):
        data=analyze([row('继续'),row('<environment_context>test',line=2),row('测试',role='assistant',line=3)])
        self.assertEqual(data['summary']['natural_messages'],1)
        self.assertEqual(data['summary']['all_records_in_filter'],3)

    def test_empty_dataset_and_gap_month_nulls(self):
        empty=analyze([])
        self.assertEqual(empty['summary']['natural_messages'],0)
        self.assertIsNone(empty['summary']['median_length'])
        self.assertEqual(empty['changes'],[])
        data=analyze([row(day='2026-01-01'),row(day='2026-03-01',line=2)])
        self.assertEqual([m['month'] for m in data['monthly']],['2026-01','2026-02','2026-03'])
        self.assertIsNone(data['monthly'][1]['word_rates']['continue'])
        self.assertEqual(data['monthly'][1]['count'],0)

    def test_timezone_changes_month_boundary(self):
        rows=[row(day='2026-01-31T23:30:00Z')]
        self.assertEqual(analyze(rows,tz='UTC')['monthly'][0]['month'],'2026-01')
        self.assertEqual(analyze(rows,tz='Asia/Shanghai')['monthly'][0]['month'],'2026-02')
        with self.assertRaises(ValueError): analyze(rows,tz='Not/A/Zone')

    def test_early_late_rates_are_weighted(self):
        rows=[]
        for month,count,hits in [(1,1,1),(2,9,0),(3,2,1),(4,2,1),(5,8,4),(6,2,2)]:
            for i in range(count):
                rows.append(row('继续' if i<hits else '其他',day=f'2026-{month:02d}-01',line=len(rows)+1))
        change=next(c for c in analyze(rows)['changes'] if c['key']=='continue')
        self.assertEqual(change['early'],10)
        self.assertEqual(change['late'],60)
        self.assertEqual(change['delta_pp'],50)
        self.assertEqual(change['early_n'],10)
        self.assertEqual(change['early_hits'],1)
        self.assertTrue(change['small_sample'])

    def test_filters_and_invalid_month_ranges(self):
        rows=[row(project='A'),row(day='2026-02-01',line=2,project='B')]
        data=analyze(rows,start='2026-02',project='B')
        self.assertEqual(data['summary']['natural_messages'],1)
        with self.assertRaises(ValueError): analyze(rows,start='2026-03',end='2026-02')
        with self.assertRaises(ValueError): analyze(rows,start='2026-13')
        self.assertEqual(month_keys('2025-12','2026-02'),['2025-12','2026-01','2026-02'])

    def test_unicode_lengths_and_multilingual_words(self):
        data=analyze([row('请继续'),row('你好🙂',line=2)])
        self.assertEqual(data['summary']['median_length'],3)
        self.assertEqual(data['summary']['short_rate'],100)
        self.assertIn('please',word_hits('Please continue'))
        self.assertNotIn('please',word_hits('请求的内容'))
        self.assertIn('verify',word_hits('VERIFY and test'))

    def test_evidence_references_and_thread_context(self):
        rows=[row('继续',source='/private/history.jsonl',line=7),row('合成回复',source='/private/history.jsonl',line=8,role='assistant')]
        result=evidence(rows,word='continue')
        self.assertEqual(result['total'],1)
        self.assertEqual(result['items'][0]['source'],'history.jsonl')
        self.assertEqual(result['items'][0]['line'],7)
        self.assertEqual(evidence(rows,thread='t1')['total'],2)
        self.assertEqual(evidence(rows,query='无匹配')['items'],[])
        with self.assertRaises(ValueError): evidence(rows,word='not-a-rule')

    def test_workflow_candidates_need_multiple_independent_threads(self):
        rows=[]
        for t in range(3):
            for i,text in enumerate(['规划范围','执行修改','测试证据']):
                rows.append(row(text,thread=f't{t}',line=len(rows)+1,day=f'2026-01-0{i+1}'))
        candidates=mine_workflows(rows)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]['support_threads'],3)
        self.assertEqual(candidates[0]['stages'],['plan','execute','verify'])
        self.assertTrue(candidates[0]['skill'].startswith('---\nname:'))
        self.assertIn('not an installed skill',candidates[0]['skill'])
        self.assertEqual(mine_workflows(rows[:6]),[])

    def test_export_privacy_allowlist_and_html_escaping(self):
        rows=[row('SECRET_UNIQUE_TEXT',source='/home/alice/private.jsonl',project='/home/alice/private-project')]
        data=analyze(rows)
        exported=json.dumps(public_analysis(data),ensure_ascii=False)
        for secret in ['SECRET_UNIQUE_TEXT','/home/alice','private-project','private.jsonl']:
            self.assertNotIn(secret,exported)
            self.assertNotIn(secret,report_markdown(data))
        data['caveats'].append('<script>alert("x")</script>')
        html=report_html(data)
        self.assertNotIn('<script>alert',html)
        self.assertIn('&lt;script&gt;',html)
        self.assertIn('2026-01',report_csv(data))

    def test_demo_is_deterministic_and_explicitly_synthetic(self):
        a=analyze(demo_messages(),mode='demo')
        b=analyze(demo_messages(),mode='demo')
        self.assertEqual(a,b)
        self.assertEqual(a['summary']['natural_messages'],3086)
        self.assertEqual(a['summary']['threads'],132)
        self.assertEqual(sum(m['count'] for m in a['monthly']),3086)
        self.assertIn('合成',a['caveats'][0])
        self.assertIn('自然用户消息：3086',report_markdown(a))
