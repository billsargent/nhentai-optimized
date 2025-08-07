# coding: utf-8
import os
import hashlib
import json
import shutil
import tempfile
from contextlib import contextmanager

from nhentai.logger import logger

def safe_filename(filename):
    """Convert a string to a safe filename"""
    # Replace problematic characters
    for char in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
        filename = filename.replace(char, '_')
    return filename

@contextmanager
def atomic_write(filepath, mode='wb', **kwargs):
    """
    Write to a file atomically (using a temporary file and rename)
    to prevent partial writes if the process is interrupted.
    
    Args:
        filepath: The target file path
        mode: File open mode, default 'wb' for binary writing
        **kwargs: Additional arguments to pass to open()
    
    Example:
        with atomic_write('/path/to/file.txt', 'w') as f:
            f.write('Hello, world!')
    """
    # Create directory if it doesn't exist
    directory = os.path.dirname(filepath)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Use the same directory as the target file for the temporary file
    # to ensure atomic rename works (must be on same filesystem)
    with tempfile.NamedTemporaryFile(
        mode=mode, dir=directory, delete=False, **kwargs
    ) as temp_file:
        try:
            # Yield the temporary file for writing
            yield temp_file
            # Flush to disk
            temp_file.flush()
            os.fsync(temp_file.fileno())
            # Close the file before renaming
            temp_file.close()
            # Atomic rename
            shutil.move(temp_file.name, filepath)
        except Exception as e:
            # Clean up the temporary file on error
            try:
                os.unlink(temp_file.name)
            except:
                pass
            raise e

def calculate_file_hash(filepath, algorithm='sha1'):
    """Calculate the hash of a file."""
    hash_obj = getattr(hashlib, algorithm)()
    
    with open(filepath, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
            
    return hash_obj.hexdigest()

def verify_file_integrity(filepath, expected_hash=None, algorithm='sha1'):
    """
    Verify file integrity by checking if it can be opened
    and optionally comparing its hash.
    
    Returns:
        bool: True if file passes integrity checks
    """
    if not os.path.exists(filepath):
        logger.warning(f"File does not exist: {filepath}")
        return False
        
    try:
        # Try to open the file to check if it's readable
        with open(filepath, 'rb') as f:
            # Read a small part to verify it's accessible
            f.read(1)
            
        if expected_hash:
            file_hash = calculate_file_hash(filepath, algorithm)
            if file_hash != expected_hash:
                logger.warning(f"File hash mismatch for {filepath}")
                return False
                
        return True
        
    except Exception as e:
        logger.error(f"Error verifying file {filepath}: {e}")
        return False
