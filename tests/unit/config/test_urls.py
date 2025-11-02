import pytest
from django.urls import resolve, reverse


@pytest.mark.parametrize(
    "url_name",
    [
        "admin:index",
    ],
)
def test_url_resolves(url_name: str) -> None:
    url = reverse(url_name)
    resolved = resolve(url)
    assert resolved.view_name == url_name
