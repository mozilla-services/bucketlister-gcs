from os import getenv

MEMCACHED_SERVER = getenv("MEMCACHED_SERVER", "localhost")
BUCKET           = getenv("GCS_PRODUCTDELIVERY_BUCKET", "moz-fx-productdelivery-pr-38b5-productdelivery")

# these paths need to end with a /
pregenerated_paths = [
        "/",
        "pub/firefox/releases/",
        "pub/firefox/candidates/",
        "pub/thunderbird/releases/",
        "pub/thunderbird/candidates/",
        ]
