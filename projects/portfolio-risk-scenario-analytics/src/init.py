"""Compatibility module retained for the requested project structure.

Python packages use ``__init__.py``; this module makes the same public helpers
available to readers who expect the literal ``init.py`` file in the brief.
"""

from . import *  # noqa: F401,F403
