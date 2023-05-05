import logging
from settings import DB_LOG_FILE

db_log = logging.getLogger(__name__)
db_log.setLevel(logging.INFO)

file_handler = logging.FileHandler(DB_LOG_FILE, mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler.setFormatter(formatter)
db_log.addHandler(file_handler)