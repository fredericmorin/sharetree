import os

# Provide required settings so test modules can be imported without a .env file.
os.environ.setdefault("SHARETREE_SESSION_SECRET", "test-secret-not-for-production")
