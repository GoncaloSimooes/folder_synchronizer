import os
from folder_synchronizer import file_operations
from folder_synchronizer.log_config import configure_logger
from folder_synchronizer.custom_errors import *
import shutil


class Synchronizer:
    def __init__(self, source_folder_path, replica_folder_path, log_directory):

        if not os.path.exists(source_folder_path):
            raise InitializationError(f"Error: The provided path for the source folder does not exist")

        if not os.path.isdir(source_folder_path):
            raise InitializationError(f"Error: {source_folder_path} is not a directory.")

        self.changed = False
        self.logger = configure_logger(log_directory)
        self.source_folder_path = source_folder_path
        self.replica_folder_path = replica_folder_path

    @staticmethod
    def _get_filenames(folder_path):
        """Returns a set of all the files in the given folder with the full path."""

        file_names = set()

        try:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    relative_path = os.path.relpath(os.path.join(root, file), folder_path)
                    file_names.add(relative_path)

        except PermissionError:
            raise GetFilenamesError(f"Error: Permission denied while accessing files in the source folder.")
        except OSError as e:
            raise GetFilenamesError(f"An unexpected error occurred while walking through the folder: {str(e)}")

        return file_names

    def _get_source_filenames(self):
        """Returns a set of all the files in the source folder with its path."""
        try:
            return self._get_filenames(self.source_folder_path)
        except GetFilenamesError as ge:
            raise GetFilenamesError(f"Error retrieving source filenames: {ge}")

    def _get_replica_filenames(self):
        """Returns a set of all the files in the replica folder with its path."""
        try:
            return self._get_filenames(self.replica_folder_path)

        except GetFilenamesError as ge:
            raise GetFilenamesError(f"Error retrieving filenames from the replica folder: {ge}")

    def _update_common_files(self):
        """ finds all file names common in both folders, compares
        it's content and replaces the ones that have been changed """
        try:
            source_file_names = self._get_source_filenames()
            replica_file_names = self._get_replica_filenames()

            common_files = source_file_names.intersection(replica_file_names)
            try:
                for file_name in common_files:
                    source_path = os.path.join(self.source_folder_path, file_name)
                    replica_path = os.path.join(self.replica_folder_path, file_name)
                    if not file_operations.compare_files(source_path, replica_path):
                        file_operations.copy_file(source_path, replica_path)
                        self.logger.info(f'File: {file_name} successfully updated.')
                        self.changed = True
            except CompareError as c:
                self.logger.error(c)

        except GetFilenamesError as ge:
            self.logger.error(f'An error occurred while retrieving filenames: {ge}')
        except PermissionError as p:
            self.logger.error(str(p))
        except OSError as o:
            self.logger.error(str(o))
        except Exception as e:
            self.logger.error(f'An unexpected error occurred during common files update: {type(e).__name__} - {str(e)}')

    def _save_missing_files(self):
        """ finds all files that exist in the source folder
        but not in the replica and copies them """
        try:
            source_files = self._get_source_filenames()
            replica_files = self._get_replica_filenames()

            try:
                missing_files = source_files.difference(replica_files)
                for file in missing_files:
                    source_path = os.path.join(self.source_folder_path, file)
                    replica_path = os.path.join(self.replica_folder_path, file)
                    file_operations.copy_file(source_path, replica_path)
                    self.logger.info(f'File: {file} successfully copied to backup.')
                    self.changed = True
            except CopyError as c:
                self.logger.error(c)

        except GetFilenamesError as ge:
            self.logger.error(f'An error occurred while retrieving filenames: {ge}')
        except PermissionError as p:
            self.logger.error(p)
        except OSError as o:
            self.logger.error(o)
        except Exception as e:
            self.logger.error(f'An unexpected error occurred during _save_missing_files: {type(e).__name__} - {e}')

    def _remove_extra_files(self):
        """finds all files that exist in the replica folder
            but not in the source and removes them"""
        try:
            source_files = self._get_source_filenames()
            replica_files = self._get_replica_filenames()

            extra_files = replica_files.difference(source_files)
            for file in extra_files:
                replica_path = os.path.join(self.replica_folder_path, file)
                os.remove(replica_path)
                self.logger.info(f'File: {file} deleted from backup folder.')
                self.changed = True

        except GetFilenamesError as ge:
            self.logger.error(f'An error occurred while retrieving filenames: {ge}')
        except PermissionError as p:
            self.logger.error(str(p))
        except OSError as o:
            self.logger.error(str(o))
        except Exception as e:
            self.logger.error(f'An unexpected error occurred during _remove_extra_files: {type(e).__name__} - {str(e)}')

    @staticmethod
    def _get_subdirectories(folder_path):
        """Returns a set of all the subdirectories inside the given folder with the relative path."""
        relative_dirs = set()

        try:
            for dirpath, _, _ in os.walk(folder_path):
                rel_path = os.path.relpath(dirpath, folder_path)
                if rel_path != '.':
                    relative_dirs.add(rel_path)

        except PermissionError:
            raise GetSubdirectoriesError(f"Error: Permission denied while accessing files in the {folder_path} folder.")
        except OSError as oe:
            raise GetSubdirectoriesError(f"An unexpected error occurred while walking through the folder: {str(oe)}")
        except Exception as e:
            raise GetSubdirectoriesError(f'An unexpected error occurred retrieving subdirectories: {type(e).__name__} - {str(e)}')

        return relative_dirs

    def _get_source_directories(self):
        """Returns a set of all the subdirectories inside the source folder with the relative path."""
        try:
            return self._get_subdirectories(self.source_folder_path)
        except GetSubdirectoriesError as g:
            raise GetSubdirectoriesError(f"Error getting source directories {g}")

    def _get_replica_directories(self):
        """Returns a set of all the subdirectories inside the replica folder with the relative path."""
        try:
            return self._get_subdirectories(self.replica_folder_path)
        except GetSubdirectoriesError as g:
            raise GetSubdirectoriesError(f"Error getting directories from replica folder {g}")

    def _check_directories(self):
        """copies any missing empty folders to the replica directory
         and deletes any directories from replica that no longer exist in source"""

        try:
            source_dirs = self._get_source_directories()
            replica_dirs = self._get_replica_directories()

            missing_dirs = source_dirs.difference(replica_dirs)
            for directory in missing_dirs:
                os.mkdir(os.path.join(self.replica_folder_path, directory))
                self.logger.info(f'Directory: {directory} created in backup folder.')

            extra_dirs = replica_dirs.difference(source_dirs)
            for directory in extra_dirs:
                shutil.rmtree(os.path.join(self.replica_folder_path, directory))
                self.logger.info(f'Directory: {directory} deleted from backup folder.')

            if missing_dirs or extra_dirs:
                self.changed = True

        except GetSubdirectoriesError as e:
            self.logger.error(f"Error getting subdirectories: {e}")
        except PermissionError as pe:
            self.logger.error(f"Error: Permission denied while accessing directories. - {pe}")
        except OSError as oe:
            self.logger.error(f"An unexpected error occurred during directory check: {oe}")
        except Exception as e:
            self.logger.error(f"An unexpected error occurred while checking subdirectories {type(e).__name__} - {e}")

    def synchronize_folders(self):
        self.changed = False

        self._check_directories()
        self._update_common_files()
        self._save_missing_files()
        self._remove_extra_files()

        if self.changed:
            self.logger.info('Synchronization complete')
        else:
            self.logger.info('No changes detected')