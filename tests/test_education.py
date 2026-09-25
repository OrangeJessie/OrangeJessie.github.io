import base64
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from education import MODULES, decrypt, encrypt, prepare_payloads


class EducationTests(unittest.TestCase):
    def test_password_and_module_isolation_and_tampering(self):
        from cryptography.exceptions import InvalidTag
        payload = encrypt('私密课程'.encode(), 'test-password', 'interview-coaching')
        self.assertEqual(decrypt(payload, 'test-password', 'interview-coaching').decode(), '私密课程')
        for password, module in [('wrong', 'interview-coaching'), ('test-password', 'ai-tutorials')]:
            with self.assertRaises(InvalidTag):
                decrypt(payload, password, module)
        corrupt = copy.deepcopy(payload)
        data = bytearray(base64.b64decode(corrupt['ciphertext']))
        data[0] ^= 1
        corrupt['ciphertext'] = base64.b64encode(data).decode()
        with self.assertRaises(InvalidTag):
            decrypt(corrupt, 'test-password', 'interview-coaching')

    def test_clean_checkout_reuse_and_changed_content_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            render = lambda text, _: (f'<p>{text}</p>', '')
            parse = lambda text: ({}, text)
            environment = {m['password_env']: 'test-password-' + key for key, m in MODULES.items()}
            with patch.dict(os.environ, environment):
                original = prepare_payloads(root, render, parse)
            files = {p: p.read_bytes() for p in root.rglob('*.json')}
            with patch.dict(os.environ, {}, clear=True):
                self.assertEqual(original, prepare_payloads(root, render, parse))
                source = root / '.private/education/interview-coaching/lesson.md'
                source.parent.mkdir(parents=True)
                source.write_text('private canary content')
                with self.assertRaises(ValueError):
                    prepare_payloads(root, render, parse)
            self.assertEqual(files, {p: p.read_bytes() for p in files})
            with patch.dict(os.environ, environment):
                updated = prepare_payloads(root, render, parse)
                self.assertEqual(updated, prepare_payloads(root, render, parse))
            self.assertIn(b'private canary content', decrypt(updated['interview-coaching'], environment['EDUCATION_INTERVIEW_PASSWORD'], 'interview-coaching'))
            self.assertFalse(any(b'private canary content' in p.read_bytes() for p in files))


if __name__ == '__main__':
    unittest.main()
