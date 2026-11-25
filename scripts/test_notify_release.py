import importlib.util
import os
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('notify_release', os.path.join(os.path.dirname(__file__), 'notify-release.py'))
assert spec and spec.loader
notify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(notify)
ENV = {'MATTERMOST_RELEASE_WEBHOOK': 'https://example.invalid/hooks/secret', 'GITHUB_REF_NAME': 'v1.2.3', 'GITHUB_REPOSITORY': 'owner/repo', 'GITHUB_SERVER_URL': 'https://github.com', 'RELEASE_URL': 'https://github.com/owner/repo/releases/tag/v1.2.3'}

class Response:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def read(self): return b'ok'

class NotifyTests(unittest.TestCase):
    @patch.dict(os.environ, ENV, clear=True)
    @patch.object(notify.urllib.request, 'urlopen', return_value=Response())
    def test_release_link_and_sender(self, send):
        notify.main()
        req = send.call_args.args[0]
        self.assertEqual(req.get_method(), 'POST')
        self.assertEqual(notify.json.loads(req.data), {'text': 'Mattermore v1.2.3 released: https://github.com/owner/repo/releases/tag/v1.2.3', 'username': 'Release Bot'})

    @patch.dict(os.environ, {**ENV, 'RELEASE_URL': 'https://example.com/bad'}, clear=True)
    @patch.object(notify.urllib.request, 'urlopen')
    def test_rejects_wrong_release(self, send):
        with self.assertRaises(ValueError): notify.main()
        send.assert_not_called()

    @patch.dict(os.environ, {**ENV, 'GITHUB_REF_NAME': 'main'}, clear=True)
    @patch.object(notify.urllib.request, 'urlopen')
    def test_rejects_non_tag(self, send):
        with self.assertRaises(ValueError): notify.main()
        send.assert_not_called()

    @patch.dict(os.environ, ENV, clear=True)
    @patch.object(notify.urllib.request, 'urlopen')
    def test_bad_body_fails(self, send):
        response = Response()
        response.read = lambda: b'bad'
        send.return_value = response
        with self.assertRaises(RuntimeError): notify.main()

    @patch.dict(os.environ, ENV, clear=True)
    @patch.object(notify.urllib.request, 'urlopen', side_effect=notify.urllib.error.URLError('https://secret'))
    def test_error_does_not_expose_url(self, send):
        with self.assertRaises(RuntimeError) as caught: notify.main()
        self.assertNotIn('secret', str(caught.exception))

if __name__ == '__main__': unittest.main()
