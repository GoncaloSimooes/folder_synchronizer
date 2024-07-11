import argparse


def parse_arguments():
    """
    Gets arguments for the source folder path, replica folder path,
    synchronization interval, and log file path, using the argparse library.
    """
    parser = argparse.ArgumentParser(description="Folder Synchronization Settings")
    parser.add_argument("--source_folder", help="Path to the source folder")
    parser.add_argument("--replica_folder", help="Path to the replica folder")
    parser.add_argument("--interval", type=int, help="Synchronization interval in seconds")
    parser.add_argument("--log_folder", help="Path to the logs folder")
    return parser.parse_args()