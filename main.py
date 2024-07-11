import time
from synchronizer import Synchronizer
from folder_synchronizer.set_command_line_args import parse_arguments
from folder_synchronizer.log_config import configure_logger
from folder_synchronizer.custom_errors import *


def main():
    args = parse_arguments()

    source_folder = args.source_folder
    replica_folder = args.replica_folder
    synchronization_interval = args.interval
    log_folder = args.log_folder

    main_logger = configure_logger(log_folder)
    try:
        # Initialize the Synchronizer object with command line arguments
        synchronizer = Synchronizer(source_folder, replica_folder, log_folder)

        while True:
            synchronizer.synchronize_folders()
            time.sleep(synchronization_interval)

    except KeyboardInterrupt:
        main_logger.info("KeyboardInterrupt. Synchronization Stopped.")
    except InitializationError as e:
        main_logger.error(str(e))


if __name__ == "__main__":
    main()