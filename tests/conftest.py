import sys
import os
import pytest

@pytest.fixture(autouse=True, scope='session')
def add_src_to_syspath():
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    # Remove standard library parser from sys.modules to force local import
    if 'parser' in sys.modules:
        del sys.modules['parser']
