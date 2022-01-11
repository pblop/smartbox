import re
import smartbox


def test_version():
    assert re.match(r"^[0-9\.]+$", smartbox.__version__)
