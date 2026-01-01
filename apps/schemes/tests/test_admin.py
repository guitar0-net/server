# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest
from django.contrib.admin import AdminSite

from apps.schemes.admin import ImageSchemeAdmin
from apps.schemes.models import ImageScheme


@pytest.mark.django_db
def test_chord_position_inline_configuration(admin_site: AdminSite) -> None:
    image_scheme_admin = ImageSchemeAdmin(ImageScheme, admin_site)
    assert image_scheme_admin.list_display == ("code", "inscription", "image")
    assert image_scheme_admin.search_fields == ("code", "inscription")
