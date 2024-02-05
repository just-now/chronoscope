import pytest
from observatory.parser import parser

def test_parser_file_not_found():
    with pytest.raises(FileNotFoundError):
        _ = parser("")

def test_parser():
    line = """
    libuv[3433]: 2055-11-29T20:57:56.489282133 conn pid: 111 sm_id: 1 started |
    """
    _ = parser("test/observatory.yaml").parse([line])
