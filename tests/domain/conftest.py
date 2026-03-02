"""Test configuration for domain unit tests.

Pre-imports app.core sub-modules in the correct order to avoid the circular
import that arises when app.core.__init__ triggers app.core.init_db before
the domain models have finished loading.
"""

import app.core.config  # noqa: F401 — must be imported before database
import app.core.database  # noqa: F401 — loads Base without triggering init_db
import app.core.logging_config  # noqa: F401
import app.core  # noqa: F401 — now safe: sub-modules already in sys.modules
