import os
import hashlib
import shutil
from folder_synchronizer.custom_errors import *


def copy_file(source_path, replica_path):
    """Copies a file from the source_path to the replica_path.
    If the directory does not exist, it creates it.
    """
    try:
        replica_dir = os.path.dirname(replica_path)
        os.makedirs(replica_dir, exist_ok=True)
        shutil.copy2(source_path, replica_path)
    except FileNotFoundError:
        raise CopyError(f"Error: The file at {source_path} does not exist.")
    except PermissionError:
        raise CopyError(f"Error: Permission denied. Unable to copy file to {replica_path}")
    except Exception as e:
        raise CopyError(f"An unexpected error occurred: {e}")


def calculate_md5(file_path):
    """Calculates the MD5 hash of a file in chunks to handle large files."""
    hash_md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def compare_files(source_file, replica_file):
    """Compares the source_file MD5 with the replica's, ensuring both files have or not the same content.
    Returns a boolean.
    """
    try:
        source_md5 = calculate_md5(source_file)
        replica_md5 = calculate_md5(replica_file)
        return source_md5 == replica_md5
    except FileNotFoundError as f:
        raise CompareError(f"Error: One of the files does not exist. Source: {source_file}, Replica: {replica_file}", f)
    except PermissionError as p:
        raise CompareError(f"Error: Permission denied while reading files. Source: {source_file}, Replica: {replica_file}", p)
    except IsADirectoryError as d:
        raise CompareError("Error: One or both paths are directories. Please provide valid file paths.", d)
    except Exception as e:
        raise CompareError(f"An unexpected error occurred: {e}")
