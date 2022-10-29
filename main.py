from flask import Flask, render_template, abort, make_response, request
from gcs import list_blobs_with_prefix
from os import path
from hashlib import sha256
import local_config
from pymemcache.client.base import Client
from pymemcache import serde

app = Flask(__name__)

cache = Client(local_config.MEMCACHED_SERVER, serde=serde.pickle_serde, connect_timeout=2, timeout=5, no_delay=True, ignore_exc=True)

@app.before_request
def before_request():
    #print(request.method, request.endpoint, request.headers, request.remote_addr)
    print(request.method, request.path)

@app.route('/')
def root():
    try:
        cache_result = cache.get_many(["_dirs", "_files"])
        dirs  = cache_result.get("_dirs", None)
        files = cache_result.get("_files", None)
    except ConnectionRefusedError:
        print(f"Got ConnectionRefusedError from memcached host {local_config.MEMCACHED_SERVER}")
    if (not dirs and not files):
        dirs, files = list_blobs_with_prefix(local_config.BUCKET, "")
    tmplt_result = render_template('listing.html', path="/", parent=None, dirs=dirs, files=files)
    resp = make_response( tmplt_result )
    resp.headers['ETag'] = sha256(tmplt_result.encode('utf-8')).hexdigest()
    return resp

@app.route('/<path:requestpath>')
def the_rest(requestpath):
    dirs = []
    files = {}
    if not requestpath.endswith("/"):
        # Seeing a lot of requests for files that shouldn't be making it here,
        # so if there's no trailing slash, let's just reject the request instead
        # of trying to fix it. The CDN shouldn't be sending any non-/ terminated
        # paths here anyway
        #requestpath += "/"
        abort(404)
    if ( requestpath in local_config.pregenerated_paths ):
        try:
            cache_result = cache.get_many([f"{requestpath}_dirs", f"{requestpath}_files"])
            dirs  = cache_result.get(f"{requestpath}_dirs", None)
            files = cache_result.get(f"{requestpath}_files", None)
        except ConnectionRefusedError:
            print(f"Got ConnectionRefusedError from memcached host {local_config.MEMCACHED_SERVER}")
    if (not dirs and not files):
        dirs, files = list_blobs_with_prefix(local_config.BUCKET, requestpath)
        if (len(dirs) == 0 and len(files.keys()) == 0):
            abort(404)
        if ( requestpath in local_config.pregenerated_paths ):
            try:
                cache.set(f"{requestpath}_dirs",  dirs, 600)
                cache.set(f"{requestpath}_files", files, 600)
            except ConnectionRefusedError:
                print(f"Got ConnectionRefusedError from memcached host {local_config.MEMCACHED_SERVER}")
    requestpath = "/" + requestpath
    parent = path.dirname(requestpath.rstrip("/")) + "/"
    if parent == "//":
        parent = "/"
    tmplt_result = render_template('listing.html', path=requestpath, parent=parent, dirs=dirs, files=files)
    resp = make_response( tmplt_result )
    resp.headers['ETag'] = sha256(tmplt_result.encode('utf-8')).hexdigest()
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
