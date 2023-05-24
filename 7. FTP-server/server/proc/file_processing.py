import configparser
import os
import pathlib
import shutil

import proc.traffic_quota as quota

config = configparser.ConfigParser()
path_to_config = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/settings.ini"
config.read(path_to_config)
PATH = pathlib.Path.home() / config.get('Server', 'DEFAULT_DIR')
WORKING_DIR = str(PATH)

common_func = {
    "mkdir": "Создание папки ---> mkdir path/to/folder",
    "rmdir": "Удаление папки ---> rmdir path/to/folder",
    "create": "Создание файла ---> create path/to/file_name",
    "rename": "Переименование файла/папки ---> rename path/to/old_name path/to/new_name",
    "remove": "Удаление файла ---> remove path/to/file"
}
spec_commands = {
    "lsdir": "Вывод содержимого текущей папки на экран",
    "upload": "Загрузка файла на сервер ---> upload path/to/file_to_upload path/to/file_on_server",
    "download": "Скачивание файла с сервера ---> download path/to/file_on_server path/to/file_to_download",
    "manual": "Выводит справку по командам",
    "exit": "Завершение работы клиента"
}


class FileProcessing:
    def __init__(self, logger, username):
        self.logger = logger
        self.username = username
        self.max_quota = int(config.get('Server', 'DEFAULT_QUOTA'))
        # os.chdir(WORKING_DIR)
        quota.create_quota_table()

    def check_quota(self):
        """Проверяет квоту трафика"""
        if quota.get_quota(self.username) < self.max_quota:
            self.logger.info(f"Доступно {self.max_quota - quota.get_quota(self.username)} байт")
            return True
        else:
            return False

    def ls(self, path):
        """Выводит содержимое директории"""
        curr_path = str(path)
        files_list = os.listdir(curr_path)
        for i in range(len(files_list)):
            if pathlib.Path(files_list[i]).is_dir():
                files_list[i] = f"*dir* {files_list[i]}"
            elif pathlib.Path(files_list[i]).is_file():
                files_list[i] = f"*file* {files_list[i]}"
        r = "\n".join(files_list)
        self.logger.info(f'Выполнен запрос списка файлов в директории {curr_path}')
        return r

    def ls_dir(self, dir_name: str):
        """Выводит содержимое указанной директории, проверяя ее существование"""
        path = PATH / dir_name
        if dir_name == 'current':
            return self.ls(PATH)
        else:
            if not path.exists():
                self.logger.info(f'Директории {dir_name} не существует')
                return False
            elif not path.is_dir():
                self.logger.info(f'{dir_name} не является директорией')
                return False
            else:
                return self.ls(path)

    def mkdir(self, dir_name: str):
        '''Создание директории'''
        if self.check_quota():
            new_dir = PATH.joinpath(dir_name)
            try:
                new_dir.mkdir(mode=0o666, parents=True)
                self.logger.info(f"Директория {dir_name} создана")
                file_size = os.path.getsize(str(new_dir))
                quota.increase_quota(self.username, file_size)
                self.logger.info(f"Доступно {self.max_quota - quota.get_quota(self.username)} байт")
                return True
            except FileExistsError:
                self.logger.info(f"Директория {dir_name} уже существует!")
                return False
        else:
            self.logger.info(f"Недостаточно места для создания директории {dir_name}")
            return False

    def rmdir(self, dir_name: str):
        '''Удаление папки по имени'''
        try:
            dir2del = PATH.joinpath(dir_name)
            file_size = os.path.getsize(str(dir2del))
            shutil.rmtree(str(dir2del), ignore_errors=False, onerror=None)
            self.logger.info(f"Директория {dir_name} удалена")
            quota.decrease_quota(self.username, file_size)
            self.logger.info(f"Доступно {self.max_quota - quota.get_quota(self.username)} байт")
            return True
        except FileNotFoundError:
            self.logger.info("Директории {dir_name} не существует")
            return False
        except NotADirectoryError:
            self.logger.info(f"Файл {dir_name} не является директорией")
            return False

    def touch(self, file_name: str):
        '''Создание пустого файла в текущей директории'''
        if self.check_quota():
            path = PATH.joinpath(file_name)
            try:
                path.touch(mode=0o666, exist_ok=False)
                self.logger.info(f"Файл {file_name} создан")
                file_size = os.path.getsize(str(path))
                quota.increase_quota(self.username, file_size)
                self.logger.info(f"Доступно {self.max_quota - quota.get_quota(self.username)} байт")
                return True
            except FileExistsError or IsADirectoryError:
                self.logger.info(f'Файл с именем {file_name} уже существует!')
                return False
        else:
            self.logger.info(f"Недостаточно места для создания файла {file_name}")
            return False

    def rename(self, old_name: str, new_name: str):
        """Переименование файлов и папок"""
        path_old = PATH.joinpath(old_name)
        path_new = PATH.joinpath(new_name)
        if path_old.exists() and not path_new.exists():
            path_old.rename(str(path_new))
            self.logger.info(f"Файл {old_name} переименован в {new_name}")
            return True
        else:
            self.logger.info(f"Что-то пошло не так. Не могу переименовать {old_name} в {new_name}")
            return False

    def rm(self, file_name: str):
        """Удаление файлов по имени"""
        path2file = PATH.joinpath(file_name).absolute()
        if path2file.is_file():
            file_size = os.path.getsize(str(path2file))
            path2file.unlink()
            self.logger.info(f"Файл {file_name} удален")
            quota.decrease_quota(self.username, file_size)
            self.logger.info(f"Доступно {self.max_quota - quota.get_quota(self.username)} байт")
            return True
        else:
            self.logger.info(f"Файла {file_name} не существует или является директорией")
            return False

    def upload_file(self, username, path: str, file_size: int, file_data: bytes):
        """Загрузка файла на сервер"""
        path2file = PATH.joinpath(path)
        if self.check_quota():
            try:
                with open(path2file, 'wb') as f:
                    f.write(file_data)
                    self.logger.info(f"Файл {path} загружен")
                    quota.increase_quota(username, file_size)
                    self.logger.info(f"Доступно {self.max_quota - quota.get_quota(self.username)} байт")
                    return True
            except FileExistsError or IsADirectoryError:
                self.logger.info(f'Файл с именем {path} уже существует!')
                return False
        else:
            self.logger.info(f"Недостаточно места для загрузки файла {path}")
            return False

    def download_file(self, path: str):
        path2file = PATH.joinpath(path)
        if path2file.exists():
            try:
                with open(path2file, 'rb') as f:
                    file_data = f.read()
                self.logger.info(f"Файл {path} выгружен для отправки клиенту")
                return file_data
            except IsADirectoryError:
                self.logger.info(f"Файл {path} является директорией")
                return False
        else:
            self.logger.info(f"Файла {path} не существует")
            return False

    @staticmethod
    def command_manual():
        man_str = "\nСписок доступных команд:\n"
        commands_str = "\n".join(
            [
                f"{key} - {value}"
                for (key, value) in common_func.items()
            ]
        )
        full_man = man_str + commands_str + "\n".join(
            [f"{another_key} - {another_value}" for (another_key, another_value) in spec_commands.items()]
        )
        return full_man

    def command_routing(self, command, *args):
        commands = [
            self.mkdir,
            self.rmdir,
            self.touch,
            self.rename,
            self.rm
        ]
        item_dict = dict(zip(common_func.keys(), commands))
        comm = item_dict.get(command)
        if comm:
            return comm(*args)
        else:
            self.logger.info(f"Команда {command} не найдена")
            return False
