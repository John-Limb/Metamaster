"""Test configuration for domain unit tests.

Pre-imports app.core sub-modules in the correct order to avoid the circular
import that arises when app.core.__init__ triggers app.core.init_db before
the domain models have finished loading.
"""

import importlib

# Side-effect imports: order matters to prevent circular import at test startup.
for _mod in (
    "app.core",
    "app.core.config",
    "app.core.database",
    "app.core.logging_config",
):
    importlib.import_module(_mod)
