"""
Shared utility functions for chunk processing.

Centralized helpers used by both PostgreSQL and Milvus services.
"""
  
def derive_has_image(image_uri: str | None) -> bool:
    """
    Derive has_image flag from image_uri.
    Returns True if image_uri is present and is an S3 URL, False otherwise.
    
    Args:
        image_uri: The image URI from the chunk payload.
    
    Returns:
        True if image_uri is a valid S3 URL, False otherwise.
    """
    return bool(image_uri and isinstance(image_uri, str) and image_uri.startswith("s3://"))
