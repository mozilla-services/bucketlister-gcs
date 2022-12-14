from google.cloud import storage
import os

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
            "last_modified": blob.updated.strftime("%Y-%m-%dT%H:%M:%SZ") , # for json responses backwards compat
        }

    for prefix in blobs.prefixes:
        stripped_name = os.path.basename(prefix.rstrip("/"))
        dirs.append(stripped_name + "/")
    dirs.sort()

    return dirs, files
