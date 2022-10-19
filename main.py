from flask import Flask, render_template, abort, make_response
from google.cloud import storage
import os
import datetime
from hashlib import sha256

app = Flask(__name__)

BUCKET = os.getenv("GCS_PRODUCTDELIVERY_BUCKET", "moz-fx-productdelivery-pr-38b5-productdelivery")

def list_blobs_with_prefix(bucket_name, prefix):
    """Lists all the blobs in the bucket that begin with the prefix.
    This can be used to list all blobs in a "folder", e.g. "public/".
    The delimiter argument can be used to restrict the results to only the
    "files" in the given "folder". Without the delimiter, the entire tree under
    the prefix is returned. For example, given these blobs:
        a/1.txt
        a/b/2.txt
    If you specify prefix ='a/', without a delimiter, you'll get back:
        a/1.txt
        a/b/2.txt
    However, if you specify prefix='a/' and delimiter='/', you'll get back
    only the file directly under 'a/':
        a/1.txt
    As part of the response, you'll also get back a blobs.prefixes entity
    that lists the "subfolders" under `a/`:
        a/b/
    """

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blobs = bucket.list_blobs(prefix=prefix, delimiter="/", fields="prefixes,items(name,size,updated),nextPageToken")

    files = {}
    dirs = []
    for blob in blobs:
        size = blob.size
        if ( size >= 1024 and size < 1024 * 1024 ):
            size = "{0:.0f}K".format(size / 1024)
        elif ( size > 1024 ):
            size = "{0:.0f}M".format(size / (1024*1024))
        stripped_name = os.path.basename(blob.name)
        files[stripped_name] = {
            "size": size,
            "updated": blob.updated.strftime("%d-%b-%Y %H:%M") ,
        }

    for prefix in blobs.prefixes:
        stripped_name = os.path.basename(prefix.rstrip("/"))
        dirs.append(stripped_name + "/")
    dirs.sort()

    if (len(dirs) == 0 and len(files.keys()) == 0):
        abort(404)

    return dirs, files

@app.route('/')
def root():
    dirs, files = list_blobs_with_prefix(BUCKET, "")
    tmplt_result = render_template('listing.html', path="/", parent=None, dirs=dirs, files=files)
    resp = make_response( tmplt_result )
    resp.headers['ETag'] = sha256(tmplt_result.encode('utf-8')).hexdigest()
    return resp

@app.route('/<path:requestpath>')
def the_rest(requestpath):
    if not requestpath.endswith("/"):
        requestpath += "/"
    dirs, files = list_blobs_with_prefix(BUCKET, requestpath)
    requestpath = "/" + requestpath
    parent = os.path.dirname(requestpath.rstrip("/")) + "/"
    if parent == "//":
        parent = "/"
    tmplt_result = render_template('listing.html', path=requestpath, parent=parent, dirs=dirs, files=files)
    resp = make_response( tmplt_result )
    resp.headers['ETag'] = sha256(tmplt_result.encode('utf-8')).hexdigest()
    return resp


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
