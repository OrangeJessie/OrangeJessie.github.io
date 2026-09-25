import base64
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from education import MODULES, decrypt, encrypt, prepare_payloads, render_module, render_locked_article
from build_static_site import parse_front_matter


class EducationTests(unittest.TestCase):
    def test_password_article_isolation_and_tampering(self):
        from cryptography.exceptions import InvalidTag
        scope = 'interview-coaching/lesson'
        payload = encrypt('私密课程'.encode(), 'test-password', scope)
        self.assertEqual(decrypt(payload, 'test-password', scope).decode(), '私密课程')
        for password, other in [('wrong', scope), ('test-password', 'ai-tutorials/lesson'), ('test-password', 'interview-coaching/other')]:
            with self.assertRaises(InvalidTag):
                decrypt(payload, password, other)
        corrupt = copy.deepcopy(payload)
        data = bytearray(base64.b64decode(corrupt['ciphertext']))
        data[0] ^= 1
        corrupt['ciphertext'] = base64.b64encode(data).decode()
        with self.assertRaises(InvalidTag):
            decrypt(corrupt, 'test-password', scope)

    def test_articles_fail_closed_reuse_and_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / '.private/education/interview-coaching/lesson.md'
            source.parent.mkdir(parents=True)
            source.write_text('---\ntitle: 公开标题\n---\nprivate canary content')
            (source.parent/'draft.md').write_text('---\ndraft: true\n---\ndraft canary')
            render = lambda text, _: (f'<p>{text}</p>', '')
            build = lambda: prepare_payloads(root, render, parse_front_matter)
            env = {'EDUCATION_INTERVIEW_PASSWORD': 'test-password'}
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ValueError):
                    build()
            with patch.dict(os.environ, env, clear=True):
                original = build()
                self.assertEqual(original, build())
            article = original['interview-coaching']['articles'][0]
            self.assertEqual(len(original['interview-coaching']['articles']), 1)
            self.assertIn(b'private canary', decrypt(article['payload'], 'test-password', 'interview-coaching/lesson'))
            listing = render_module('interview-coaching', original['interview-coaching'])
            gate = render_locked_article('interview-coaching', article)
            self.assertIn('历史咨询', listing)
            self.assertNotIn('data-unlock-form', listing)
            self.assertIn('/interview-coaching/lesson/', listing)
            self.assertIn('data-unlock-form', gate)
            self.assertNotIn('private canary', listing + gate)
            self.assertNotIn('<h2>公开标题</h2>', gate)
            files = {p:p.read_bytes() for p in root.rglob('*.json')}
            with patch.dict(os.environ, {}, clear=True):
                source.write_text('updated secret')
                with self.assertRaises(ValueError):
                    build()
                self.assertEqual(files, {p:p.read_bytes() for p in files})
                shutil.rmtree(root/'.private')
                self.assertEqual(original, build())
                source.parent.mkdir(parents=True)
                self.assertEqual(build()['interview-coaching']['articles'], [])
            self.assertFalse(any(b'private canary' in data for data in files.values()))

    def test_history_is_collapsed_and_module_has_no_password_gate(self):
        page = render_module('interview-coaching', {'articles': []})
        self.assertIn('<details class="education-history">', page)
        self.assertNotIn('<details open', page)
        self.assertEqual(page.count('<img '), 2)
        self.assertNotIn('data-unlock-form', page)
        self.assertNotIn('data-unlock-form', render_module('ai-tutorials', {'articles': []}))


if __name__ == '__main__':
    unittest.main()
