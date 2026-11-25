#!/usr/bin/env python3
"""Send a published release link to the configured Mattermost webhook."""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main():
    webhook = os.environ['MATTERMOST_RELEASE_WEBHOOK']
    release = os.environ['RELEASE_URL']
    tag = os.environ['GITHUB_REF_NAME']
    repo = os.environ['GITHUB_REPOSITORY']
    server = os.environ['GITHUB_SERVER_URL'].rstrip('/')
    expected = f"{server}/{repo}/releases/tag/{urllib.parse.quote(tag, safe='')}"
    if not webhook or not tag.startswith('v') or release != expected:
        raise ValueError('Missing webhook or unexpected release URL')
    text = f'Mattermore {tag} released: {release}'
    if os.environ.get('NOTIFY_TEST') == '1':
        text = f'Test notification (no new release): {release}'
    req = urllib.request.Request(webhook, data=json.dumps({'text': text, 'username': 'Release Bot'}).encode(), headers={
        'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0 (compatible; release-notifier/1.0)',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200 or response.read().strip() != b'ok':
                raise RuntimeError('Mattermost returned an unexpected response')
    except urllib.error.URLError:
        raise RuntimeError('Mattermost webhook request failed') from None
    print('Release notification accepted by Mattermost')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, ValueError, RuntimeError) as exc:
        print(f'Release notification failed: {exc}', file=sys.stderr)
        sys.exit(1)
