import importlib.util
from pathlib import Path
from urllib.request import Request

import pytest


SCRIPT = Path(__file__).parents[3] / "scripts" / "acquire_official_snapshot.py"
SPEC = importlib.util.spec_from_file_location("acquire_official_snapshot", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_redirect_handler_rejects_non_approved_destination():
    handler = MODULE.ApprovedDomainRedirectHandler()

    with pytest.raises(ValueError, match="unapproved download domain"):
        handler.redirect_request(
            Request(MODULE.DOWNLOAD_URL),
            None,
            302,
            "Found",
            {},
            "http://127.0.0.1/private.csv",
        )


def test_redirect_handler_allows_approved_https_destination():
    handler = MODULE.ApprovedDomainRedirectHandler()

    redirected = handler.redirect_request(
        Request(MODULE.DOWNLOAD_URL),
        None,
        302,
        "Found",
        {},
        "https://data.go.th/approved.csv",
    )

    assert redirected.full_url == "https://data.go.th/approved.csv"
