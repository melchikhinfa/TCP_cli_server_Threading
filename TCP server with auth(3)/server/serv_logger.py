import logging

server_logger = logging.getLogger(__name__)
server_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("./logs/server.log", mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler.setFormatter(formatter)
server_logger.addHandler(file_handler)