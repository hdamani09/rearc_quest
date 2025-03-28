def get_bucket_and_key(url : str):
    if url.startswith('s3://'):
        bucket, key = url[5:].split("/", 1)
    else:
        bucket, key = url.split("/", 1)
    return bucket, key