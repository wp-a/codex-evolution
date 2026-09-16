import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from codex_evolution.cli import main

class CliTests(unittest.TestCase):
    def test_demo_report_written_and_prompt_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);report=root/'report.html';prompt=root/'audit-prompt.md'
            with contextlib.redirect_stdout(io.StringIO()):
                main(['--db',str(root/'app.sqlite'),'report','--demo','--format','html','--out',str(report)])
                main(['prompt','instruction-audit','--out',str(prompt)])
            self.assertIn('3,086',report.read_text())
            self.assertIn('更改任何文件之前',prompt.read_text())

    def test_audit_refuses_to_overwrite_input(self):
        with tempfile.TemporaryDirectory() as folder:
            agents=Path(folder)/'AGENTS.md';agents.write_text('每一步都必须先确认。',encoding='utf-8')
            before=agents.read_bytes()
            with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as exc:
                main(['audit',str(agents),'--out',str(agents)])
            self.assertEqual(exc.exception.code,1)
            self.assertEqual(agents.read_bytes(),before)

    def test_skill_command_creates_review_drafts_only(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);drafts=root/'review-drafts'
            with contextlib.redirect_stdout(io.StringIO()):
                main(['--db',str(root/'app.sqlite'),'skills','--demo','--out',str(drafts)])
            files=list(drafts.glob('*/SKILL.md'))
            self.assertEqual(len(files),8)
            self.assertIn('not an installed skill',files[0].read_text())
            self.assertFalse((root/'.agents').exists())

    def test_doctor_does_not_print_secret_key(self):
        from unittest.mock import patch
        with patch.dict('os.environ',{'OPENAI_API_KEY':'test-secret-must-not-appear','CODEX_EVOLUTION_MODEL':'example-model'}):
            output=io.StringIO()
            with contextlib.redirect_stdout(output): main(['doctor'])
        data=json.loads(output.getvalue())
        self.assertTrue(data['optional_model']['available'])
        self.assertNotIn('test-secret-must-not-appear',output.getvalue())
