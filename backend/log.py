import os
import sys

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)

# Get the absolute path of the current file
current_file_path = os.path.abspath(__file__)
# Get the directory path of the current file
current_dir_path = os.path.dirname(current_file_path)
# Get the parent directory path
parent_dir_path = os.path.dirname(current_dir_path)
# Add the parent directory path to the sys.path
sys.path.insert(0, parent_dir_path)

import logging

# Create a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

#####################  local saving  #####################
log_file_path = "./application.log"
# Delete the log file if it already exists
if os.path.exists(log_file_path):
    os.remove(log_file_path)

# Configure the logger
logger2 = logging.getLogger(__name__)
handler = logging.FileHandler(log_file_path, encoding="utf-8")
handler.setLevel(logging.DEBUG)

# Create a formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)

logger2.addHandler(handler)

# Optional: Set logger level
logger2.setLevel(logging.DEBUG)

# Example log messages
logger2.info("This is an info message.")
logger2.debug("This is a debug message.")
