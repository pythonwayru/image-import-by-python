#!/usr/bin/env python3

import sys
import os
# На всякий случай подстрахуемся от отсутствия ExifRead`а.
try:
    import exifread
except ImportError:
    sys.exit("Для работы скрипта необходим модуль EXIFREAD, \
            а он у вас, похоже, не установлен. \
             \nЗадание не выполнено.")

DEFAULT_OUTPUT = '/full/path/to/photoarchive_dir'

def confirm():
    while True:
        answer = input('Приступаем: [Y]/n? ').lower()
        if answer in ['', 'y']:
            return True
        elif answer == 'n':
            return False

def getDirs(args, default=''):
    while True:
        argsCount = len(args)
        if argsCount > 1:
            if os.path.isdir(args[1]):
                dirs = [args[1]]
            else:
                args[1] = input(
                    'Исходный путь для импорта не верен, задайте правильный: ')
                continue
            if argsCount >= 3:
                dirs.append(args[2])
            else:
                dirs.append(default)
                args.append(dirs[1])
            try:
                os.makedirs(dirs[1], exist_ok=True)
                break
            except PermissionError:
                args[2] = input(
                    'Целевой каталог не доступен на запись, задайте другой: ')
        else:
            # Если скрипт запущен без аргументов, то просим это исправить.
            args.append(input("Задайте исходный каталог: "))
    return dirs


def main():
    # Получаем исходную и целевую дирректории.
    dirsList = getDirs(sys.argv, DEFAULT_OUTPUT)
    # Показываем куда и откуда будет импорт.
    print('Источник импорта: ', dirsList[0])
    print('Дирректория назначения: ', dirsList[1])
    # Просим подтверждение перед началом работы.
    if not confirm():
        sys.exit("Задание отменено")

    # Задаем счетчики "плохих" и "хороших" операций.
    fTotal = okOp = badOp = 0
    badFiles = []
    # Собственно, импорт.
    for root, dirs, files in os.walk(dirsList[0]):
        i = 0
        for name in files:
            i += 1
            fTotal += 1
            filePath = os.path.join(root, name)
            # Отображаем текущий процесс и прогресс выполнения.
            print('Обработка файла {} из {} (дир. -= {} =-)'
                  .format(i, len(files), os.path.basename(root).upper()))
            with open(filePath, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                exifDateTime = tags.get('EXIF DateTimeOriginal')

                # При отсутствии у фото EXIF-данных - файл пропускаем,
                # занося его в список "плохих" файлов.
                if not exifDateTime:
                    print('Отсутствуют EXIF данные. Файл пропущен!!!', name)
                    badOp += 1
                    badFiles.append(filePath)
                    continue

            exifDate, exifTime = str(exifDateTime).split(' ')
            year, month, day = exifDate.split(':')
            hour, minute, sec = exifTime.split(':')

            fileExtension = os.path.splitext(name)[1]
            # Задаем название импортированного файла.
            newFileName = '{}-{}-{}_{}{}'.format(hour,
                                                 minute, sec, i, fileExtension)
            path = dirsList[1] + \
                '/{}/{}/{}'.format(year, month, day).replace('//', '/')

            if not os.path.exists(path):
                print('Создаем новую папку')
                os.makedirs(path, exist_ok=True)

            newPath = os.path.join(path, newFileName)
            doCopy = os.system("cp {} {}".format(
                filePath.replace(' ', '\ '), newPath))

            if doCopy == 0:
                print('OK')
                okOp += 1
            else:
                print('BAD')
                badOp += 1
    # По завершении импорта выводим статистику сделанного.
    print('Обработано файлов всего:', fTotal)
    print('Успешных операций:', okOp)
    print('Завершенных с ошибками:', badOp)
    # И имена "плохих" файлов, если таковые есть.
    if len(badFiles):
        print('Необработанные файлы: ')
        for bf in badFiles:
            print(bf)


if __name__ == '__main__':
    main()
