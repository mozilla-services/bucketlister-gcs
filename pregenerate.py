from pymemcache.client.base import Client
from pymemcache import serde
from gcs import list_blobs_with_prefix
import local_config
from os import getenv

cache = Client(local_config.MEMCACHED_HOST, serde=serde.pickle_serde)

def cache_dir(path):
    dirs = []
    files = {}
    dirs, files = list_blobs_with_prefix(local_config.BUCKET, path)
    cache.set(f"{path}_dirs", dirs)
    cache.set(f"{path}_files", files)

if __name__ == '__main__':
    for path in local_config.pregenerated_paths:
        print(f"Fetching & caching {path}")
        cache_dir(path)
