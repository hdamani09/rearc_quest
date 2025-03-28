def get_bucket_and_key(url : str):
    """
    Extracts the bucket and key from an S3 path

    Args:
        url (str): The S3 file path

    Returns:
        tuple[str, str]: The bucket and key
    """
    if url.startswith('s3://'):
        bucket, key = url[5:].split("/", 1)
    else:
        bucket, key = url.split("/", 1)
    return bucket, key