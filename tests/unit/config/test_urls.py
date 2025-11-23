# SPDX-FileCopyrightText: 2025 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

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
