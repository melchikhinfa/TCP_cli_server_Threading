import logging

cli_log = logging.getLogger(__name__)
cli_log.setLevel(logging.INFO)

file_handler = logging.FileHandler("../logs/cli.log", mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler.setFormatter(formatter)
cli_log.addHandler(file_handler)