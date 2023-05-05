import logging

db_log = logging.getLogger(__name__)
db_log.setLevel(logging.INFO)

file_handler = logging.FileHandler("./logs/db.log", mode="a")
formatter = logging.Formatter("%(asctime)s %(levelname)s %(funcName)s: %(message)s")

file_handler.setFormatter(formatter)
db_log.addHandler(file_handler)