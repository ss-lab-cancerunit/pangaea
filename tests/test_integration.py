""" Module containing basic integration testing


Only basic integration testing, because calling the tool multiple
times would slow down testing and potentially annoy Entrez for spamming
too many requests.

There is some API mocking in other tests, but I wanted to keep the integration
as close to reality as possible i.e. if the API doesn't work, the test should 
also fail.
"""

import tempfile
from subprocess import Popen, PIPE


TOOL = 'pangaea/download.py'


def run_tool(args):
    p = Popen(args, stdout=PIPE, stderr=PIPE)
    stdout, stderr = (out.decode('utf-8') for out in p.communicate())
    return p, stdout, stderr


def test_download_tp53_default_args():
    p, stdout, stderr = run_tool([TOOL, 'tp53', '--output', tempfile.mkstemp()[-1]])
    assert p.returncode == 0
    assert not stderr 

