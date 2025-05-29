import os

config = os.getenv("CONFIG")
if not config:
    raise ValueError("CONFIG environment variable not found!")

print("CONFIG wurde geladen.")
