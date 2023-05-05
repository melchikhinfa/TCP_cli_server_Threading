import logging

CLIENT_LOG_FILE = '../logs/client.log'
cli_log = logging.getLogger(__name__)
cli_log.setLevel(logging.INFO)

file_handler = logging.FileHandler(CLIENT_LOG_FILE, mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler.setFormatter(formatter)
cli_log.addHandler(file_handler)