import pytest
from chronoscope.parser import parser

def test_parser_file_not_found():
    with pytest.raises(FileNotFoundError):
        _ = parser("")

def test_parser():
    line = """
    libuv[3433]: 2055-11-29T20:57:56.489282133 conn pid: 111 sm_id: 1 started |
    """
    _ = parser("test/chronoscope.yaml").parse([line])

def test_parser_malformed():
    line = """
    libuv[3433]: 2055-11-29T20:57:56.667095559 conn
    """
    _ = parser("test/chronoscope.yaml", verbose=True).parse([line])

def test_parser_fuzz():
    line = """
a b c d
    """
    _ = parser("test/chronoscope.yaml").parse([line])

def test_parser_empty():
    line = ""
    _ = parser("test/chronoscope.yaml").parse([line])
