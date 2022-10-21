from pymemcache.client.base import Client
from pymemcache import serde
from gcs import list_blobs_with_prefix
import local_config
from os import getenv
from threading import Thread
from time import perf_counter

cache = Client(local_config.MEMCACHED_SERVER, serde=serde.pickle_serde, connect_timeout=10, timeout=60, no_delay=True, ignore_exc=True)

def cache_dir(path):
    print(f"Fetching & caching {path}")
    start_time = perf_counter()
    dirs = []
    files = {}
    dirs, files = list_blobs_with_prefix(local_config.BUCKET, path)
    cache.set(f"{path}_dirs", dirs, 600)
    cache.set(f"{path}_files", files, 600)
    end_time = perf_counter()
    print(f'{path} took {end_time- start_time: 0.2f} second(s) to complete')

if __name__ == '__main__':
    # TODO: do these in parallel
    threads = []
    for path in local_config.pregenerated_paths:
        new_thread = Thread(target=cache_dir,args=(path,))
        threads.append(new_thread)
        new_thread.start()
    for thread in threads:
        thread.join()
