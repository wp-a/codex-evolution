import tempfile
import unittest
from pathlib import Path
from codex_evolution.audit import audit_instructions, audit_plan, load_files

class AuditTests(unittest.TestCase):
    def test_conflict_quotes_diffs_and_permission_flags(self):
        text='# Rules\n- 在已授权范围内自主推进。\n- 每一步都必须先向用户确认。\n- 生产部署前必须获得明确批准。\n'
        result=audit_instructions([{'path':'AGENTS.md','text':text}])
        rules={f['rule'] for f in result['findings']}
        self.assertIn('blanket-confirmation',rules)
        self.assertIn('autonomy-conflict',rules)
        blanket=next(f for f in result['findings'] if f['rule']=='blanket-confirmation')
        self.assertEqual(blanket['line'],3)
        self.assertEqual(blanket['quote'],'- 每一步都必须先向用户确认。')
        self.assertTrue(blanket['permission_expansion'])
        self.assertEqual(blanket['intent'],'needs-review')
        self.assertEqual(len(result['protected']),1)
        diff=result['diffs'][0]['diff']
        self.assertIn('--- a/AGENTS.md',diff)
        self.assertNotIn('-- 生产部署',diff)
        self.assertEqual(result['diffs'][0]['status'],'proposal-only')

    def test_sensitive_approval_and_integrity_hashes_preserved(self):
        text='生产部署、删除数据前必须批准。\n下载的发布制品必须核验 SHA256 完整性。'
        result=audit_instructions([{'path':'AGENTS.md','text':text}])
        self.assertEqual(result['summary']['findings'],0)
        self.assertEqual(result['summary']['preserved'],2)
        self.assertEqual(result['diffs'],[])

    def test_override_shadows_same_directory_agents(self):
        files=[{'path':'AGENTS.md','text':'每一步都必须向用户确认。'},
               {'path':'AGENTS.override.md','text':'在已授权范围内自主推进。'}]
        result=audit_instructions(files)
        self.assertFalse(result['files'][0]['active'])
        self.assertEqual(result['findings'],[])
        files[1]['text']='   '
        self.assertTrue(audit_instructions(files)['files'][0]['active'])

    def test_sibling_scopes_do_not_create_false_autonomy_conflicts(self):
        files=[{'path':'frontend/AGENTS.md','text':'每一步都必须先确认。'},
               {'path':'backend/AGENTS.md','text':'自主推进并完成已授权任务。'}]
        result=audit_instructions(files)
        self.assertNotIn('autonomy-conflict',{f['rule'] for f in result['findings']})
        files[1]['path']='AGENTS.md'
        result=audit_instructions(files)
        self.assertIn('autonomy-conflict',{f['rule'] for f in result['findings']})

    def test_skill_conflicts_are_conditional(self):
        files=[{'path':'AGENTS.md','text':'每一步都必须先确认。'},
               {'path':'.agents/skills/example/SKILL.md','text':'---\nname: example\ndescription: Do a scoped review.\n---\n自主推进已授权任务。'}]
        result=audit_instructions(files)
        conflict=next(f for f in result['findings'] if f['rule']=='autonomy-conflict')
        self.assertIn('Skill 被加载',conflict['impact'])
        self.assertNotIn('skill-metadata',{f['rule'] for f in result['findings']})

    def test_missing_skill_metadata_and_completion_conflict(self):
        result=audit_instructions([{'path':'SKILL.md','text':'# Draft\n仅提供计划，不要执行。\n必须完成实现并交付结果。'}])
        self.assertIn('skill-metadata',{f['rule'] for f in result['findings']})
        self.assertIn('completion-conflict',{f['rule'] for f in result['findings']})

    def test_vague_stop_and_blanket_hash(self):
        result=audit_instructions([{'path':'AGENTS.md','text':'遇到不确定细节时必须停止。\n每次修改都执行 SHA256 哈希比较。'}])
        rules={f['rule'] for f in result['findings']}
        self.assertIn('vague-stop',rules)
        self.assertIn('blanket-hash',rules)

    def test_negative_anti_bloat_requirements_are_not_flagged(self):
        result=audit_plan('目标：统计本机记录。\n范围：只做本机。\n验收：可重算。\n不要重复哈希比较。\n避免多轮审核和 Gate。\n无需增加多层兜底。')
        self.assertEqual(result['findings'],[])
        self.assertEqual(result['missing_context'],[])

    def test_plan_questions_preserve_protections(self):
        result=audit_plan('每个步骤检查 SHA256。\n设置三个 Gate。\n增加多层兜底。\n先建立微服务与事件总线。\n生产部署前必须批准。\n下载的发布制品验证 SHA256 完整性。')
        self.assertEqual(len(result['findings']),4)
        self.assertEqual(len(result['protected']),2)
        self.assertEqual(result['diffs'],[])
        self.assertTrue(all(not f['permission_expansion'] for f in result['findings']))
        self.assertTrue(result['missing_context'])

    def test_filesystem_audit_does_not_modify_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);agents=root/'AGENTS.md';agents.write_text('每一步都必须先向用户确认。',encoding='utf-8')
            (root/'notes.txt').write_text('not an instruction file')
            original=agents.read_bytes()
            files,warnings=load_files(root)
            self.assertEqual([f['path'] for f in files],['AGENTS.md'])
            audit_instructions(files)
            self.assertEqual(original,agents.read_bytes())
            self.assertFalse((root/'AGENTS.override.md').exists())
            self.assertEqual(warnings,[])

    def test_invalid_input_limits(self):
        with self.assertRaises(ValueError): audit_instructions([{'path':'a','text':123}])
        with self.assertRaises(ValueError): audit_instructions([{'path':'AGENTS.md','text':'x'*70000}])
        with self.assertRaises(ValueError): audit_plan('x'*64001)
