"""Test doubles."""

import json
import re
from urllib.parse import parse_qs, urlparse

import httplib2


class FakeHttp:
    """Answers API calls from a table and records them."""

    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def request(self, uri, method="GET", body=None, headers=None, **_):
        parsed = urlparse(uri)
        self.calls.append(
            (method, parsed.path, parse_qs(parsed.query), json.loads(body or "null"))
        )
        key = (method, re.sub(r"^/v[12]/", "", parsed.path))
        content = self.responses[key]
        if callable(content):
            content = content()
        return httplib2.Response({"status": "200"}), json.dumps(content).encode()
