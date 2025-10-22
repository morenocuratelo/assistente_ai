"""
Make the tests directory a package so local imports like
`from tests.conftest import ...` resolve to the repository package and not
to any installed package named `tests` in the virtualenv.

This file is intentionally minimal.
"""

__all__ = []
