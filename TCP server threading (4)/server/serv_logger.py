import logging
from settings import SERVER_LOG_FILE
import pathlib as pl

server_logger = logging.getLogger(__name__)
server_logger.setLevel(logging.INFO)

path_to_log = SERVER_LOG_FILE

formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler = logging.FileHandler(path_to_log, mode="a")
file_handler.setFormatter(formatter)
server_logger.addHandler(file_handler)

# Поток вывода в консоль
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)


def change_stream_logs():
    if stream_handler not in server_logger.handlers:
        server_logger.addHandler(stream_handler)
        server_logger.info("Включен вывод логов в консоль")
    else:
        server_logger.removeHandler(stream_handler)
        server_logger.info("Вывод логов в консоль отключен")
        print("Вывод логов в консоль отключен")
