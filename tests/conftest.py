"""Shared pytest fixtures/config for Wellspring's test suite.

``scripts/`` is invoked directly by the Makefile (``python scripts/foo.py``),
not imported as an installed package, so it isn't on ``sys.path`` by
default under pytest's import mode. Add it once here rather than having
every test module repeat a path hack -- see the constitution's Article XI
(Package Ownership & One Class Per File) for why ``scripts/`` isn't a
proper ``__init__.py``-owned package yet.
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
