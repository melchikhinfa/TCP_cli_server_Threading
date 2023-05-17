import os
import pathlib
import shutil
from settings import WORKING_DIR, PATH

commands_dct = {
            "cd": "Перемещение между папками",
            "ls": "Вывод содержимого текущей папки на экран",
            "mkdir": "Создание папки",
            "rmdir": "Удаление папки",
            "create": "Создание файла",
            "rename": "Переименование файла/папки",
            "read": "Чтение файла",
            "remove": "Удаление файла",
            "copy": "Копирование файла/папки",
            "move": "Перемещение файла/папки",
            "write": "Запись в файл",
            "cwd": "Показать текущую директорию",
            "manual": "Вывести список команд"
        }

class FileManager:

    def __int__(self):
        pass

    def ls(self):
        """Выводит содержимое директории"""
        curr_path = str(pathlib.Path.cwd())
        files_list = os.listdir(curr_path)
        for i in range(len(files_list)):
            if pathlib.Path(files_list[i]).is_dir():
                files_list[i] = f"*dir* {files_list[i]}"
            elif pathlib.Path(files_list[i]).is_file():
                files_list[i] = f"*file* {files_list[i]}"
        r = "\n".join(files_list)
        print(f"Содержимое {curr_path}:\n{r}")

    def cd(self, dir_name: str):
        curr_path = str(pathlib.Path.cwd())
        if WORKING_DIR in curr_path:
            try:
                os.chdir(os.path.join(curr_path, dir_name))
            except FileNotFoundError or NotADirectoryError:
                print(f"Директории {dir_name} не существует или \
                      файл {dir_name} не является директорией")
        elif WORKING_DIR in curr_path and WORKING_DIR != curr_path and dir_name == "..":
            curr_path = str(pathlib.Path.cwd().parent)
            os.chdir(curr_path)
        else:
            print("Вы пытаетесь выйти за пределы рабочей директории. \
                  А ну-ка брысь отсюда!")

    def pwd(self):
        print(str(pathlib.Path.cwd()))

    def manual(self):
        commands_str = "\n".join(
            [
                f"{key} - {value}"
                for (key, value) in commands_dct.items()
            ]
        )
        print(f"Список команд:\n{commands_str}")

    def mv(self, src: str, dst: str):
        "Перемещние файла/папки из src в dst"
        try:
            path2src = pathlib.Path(WORKING_DIR).joinpath(src)
            path2dst = pathlib.Path(WORKING_DIR).joinpath(dst)
            shutil.move(path2src, path2dst)
        except shutil.Error:
            print(f"Не могу переместить в {dst}, т.к. он не является папкой!")
        except FileNotFoundError:
            print(f"Файл (директория) {src} не найдена!")

    def cp(self, src: str, dst: str):
        """Копирование файлов из одной папки в другую"""
        path2src = pathlib.Path(WORKING_DIR).joinpath(src)
        path2dst = pathlib.Path(WORKING_DIR).joinpath(dst)
        for item in os.listdir(str(path2src)):
            src_dir = path2src.joinpath(item)
            dst_dir = path2dst.joinpath(item)
            if src_dir.is_dir():
                shutil.copytree(
                    str(src_dir), str(dst_dir),
                    symlinks=False, ignore_dangling_symlinks=True,
                    dirs_exist_ok=True
                )
            else:
                shutil.copy2(str(src_dir), dst_dir)

    def mkdir(self, dir_name: str):
        '''Создание директории'''
        new_dir = pathlib.Path(WORKING_DIR).joinpath(dir_name)
        try:
            new_dir.mkdir(mode=0o666, parents=True)
        except FileExistsError:
            print(f"Директория {dir_name} уже существует!")

    def rmdir(self, dir_name: str):
        '''Удаление папки по имени'''
        try:
            dir2del = PATH.joinpath(dir_name)
            shutil.rmtree(str(dir2del), ignore_errors=False, onerror=None)
        except FileNotFoundError:
            print(f"Директории {dir_name} не существует")
        except NotADirectoryError:
            print(f"Файл {dir_name} не является директорией")

    def touch(self, file_name: str):
        '''Создание пустого файла в текущей директории'''
        path2file = pathlib.Path.cwd() / file_name
        try:
            path2file.touch(mode=0o666, exist_ok=False)
        except FileExistsError or IsADirectoryError:
            print(f'Файл с именем {file_name} уже существует!')

    def rename(self, old_name: str, new_name: str):
        """Переименование файлов и папок"""
        path_old = pathlib.Path(old_name)
        path_new = pathlib.Path(new_name)
        if path_old.exists() and not path_new.exists():  # проверяем, что новое имя не занято
            path_old.rename(str(path_new))
        else:
            print(f"Что-то пошло не так. Не могу переименовать {old_name} в {new_name}")

    def rm(self, file_name: str):
        """Удаление файлов по имени"""
        path2file = pathlib.Path(file_name).absolute()
        if path2file.is_file():
            path2file.unlink()
        else:
            print(f"Файла {file_name} не существует или является директорией")

    def write(self, file_name: str, *data: str):
        """Запись текста в файл"""
        data2write = " ".join(data)
        path2file = pathlib.Path(WORKING_DIR).joinpath(file_name)
        if path2file.is_file():
            path2file.write_text(data2write)
        else:
            print(f"Файла {file_name} не существует или является директорией")

    def cat(self, file_name: str):
        path2file = pathlib.Path(WORKING_DIR).joinpath(file_name)
        if path2file.is_file():
            print(path2file.read_text())
        else:
            print(f"Файла {file_name} не существует или является директорией")

    def router(self, command: str):
        """Ассоциация между командами и методами FileManager"""
        commands = [
            self.cd,
            self.ls,
            self.mkdir,
            self.rmdir,
            self.touch,
            self.rename,
            self.cat,
            self.rm,
            self.cp,
            self.mv,
            self.write,
            self.pwd,
            self.manual
        ]
        item_dict = dict(zip(commands_dct.keys(), commands))
        return item_dict.get(command, None)


f = FileManager()
os.chdir('/home/andreymelchikhin/WORKING_DIRECTORY')
f.pwd()
