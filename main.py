from flask import Flask, render_template, abort, make_response
from gcs import list_blobs_with_prefix
from os import path
from hashlib import sha256
import local_config
from pymemcache.client.base import Client
from pymemcache import serde

app = Flask(__name__)

cache = Client(local_config.MEMCACHED_HOST, serde=serde.pickle_serde)

@app.route('/')
def root():
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
        requestpath += "/"
    if ( requestpath in local_config.pregenerated_paths ):
        try:
            dirs  = cache.get(f"{requestpath}_dirs")
            files = cache.get(f"{requestpath}_files")
        except ConnectionRefusedError:
            pass
    if (not dirs and not files):
        dirs, files = list_blobs_with_prefix(local_config.BUCKET, requestpath)
        if (len(dirs) == 0 and len(files.keys()) == 0):
            abort(404)
        if ( requestpath in local_config.pregenerated_paths ):
            try:
                cache.set(f"{requestpath}_dirs",  dirs)
                cache.set(f"{requestpath}_files", files)
            except ConnectionRefusedError:
                pass
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
