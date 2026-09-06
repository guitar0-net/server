# SPDX-FileCopyrightText: 2026 Andrey Kotlyar <guitar0.app@gmail.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Database reads backing the operational endpoints."""

from django.db import DatabaseError, connection


def is_database_reachable() -> bool:
    """Check whether the default database answers a trivial query.

    Returns:
        True when the query succeeds, False when the database is unreachable
        or refuses it.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except DatabaseError:
        return False
    return True
