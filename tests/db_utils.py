"""Shared database utilities for the test suite."""

import os

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://test:test@localhost:5432/metamaster_test",
)
