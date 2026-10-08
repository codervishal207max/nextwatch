import os

# Must run before the app is imported: tests use an in-memory DB, never the dev database.
os.environ["DATABASE_URL"] = "sqlite://"
