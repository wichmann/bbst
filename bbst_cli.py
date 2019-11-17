#! /usr/bin/env python3

"""
bbst - BBS Teacher Management

@author: Christian Wichmann
"""

import sys
import shutil
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, astuple, replace

import click
from tabulate import tabulate
from prompt_toolkit import PromptSession, prompt
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import Completer, Completion, WordCompleter, PathCompleter, merge_completers
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import message_dialog, yes_no_dialog, input_dialog, ProgressBar
from prompt_toolkit.history import FileHistory

from bbst.data import Teacher, generate_mail_address, generate_username
from bbst.fileops import read_bbsv_file, read_teacher_list, write_teacher_list
from bbst.pdf import create_user_info_document


logger = logging.getLogger('bbst')


LOG_FILENAME = 'bbst.log'
REPO_TOKEN = '.bbst'
TEACHER_LIST_FILENAME = 'teacher_list.csv'
HISTORY_FILE = '.bbst-history-file'
USER_INFO_FILENAME = 'Anschreiben.pdf'
BASE_PATH = Path().cwd()

# TODO: Eliminate global variables!
current_path = BASE_PATH
current_repo = ''


################################  Helper ######################################

def list_all_repos():
    return [d for d in BASE_PATH.iterdir() if d.is_dir() and (d/REPO_TOKEN).exists()]

def add_new_teacher(new_teacher):
    current_repo_list = current_path / TEACHER_LIST_FILENAME
    l = read_teacher_list(current_repo_list)
    l.append(new_teacher)
    write_teacher_list(l, current_repo_list)

def import_repo_into_repo(import_repo, destination_repo):
    """
    Reads a given import file in CSV format and copies it into a given directory.
    """
    # TODO: Expand function to import user from file if teachers list already exists
    # TODO: Change function to import teachers and remove users marked as deleted and reset added flag!!!!!
    destination_file = BASE_PATH / destination_repo / TEACHER_LIST_FILENAME
    source_file = BASE_PATH / import_repo / TEACHER_LIST_FILENAME
    if destination_file.exists():
        print('Fehler: Liste existiert bereits in angegebenen Repo.')
        return
    shutil.copy(source_file, destination_file)

################################  Handler #####################################

def create_repo(args):
    if current_repo:
        print('Fehler: Bitte verlassen sie zuerst das aktuelle Repo.')
        return
    default_new_repo_name = datetime.today().strftime('%Y-%m-%d')
    new_repo_name = args[0] if args else default_new_repo_name
    # check whether dir exists
    new_repo_path = Path('.') / new_repo_name
    if new_repo_path.exists():
        print('Fehler: Verzeichnis existiert schon.')
        return
    # create directory for repo and add token file
    new_repo_path.mkdir()
    t = new_repo_path / REPO_TOKEN
    t.touch()
    open_repo([new_repo_name])
    # check whether to import user from different repo into new repo
    if len(args) == 3 and args[1] == 'from':
        import_file = args[2]
        if not Path(import_file).exists():
            print('Fehler: Angegebene Importdatei konnte nicht gefunden werden.')
            return
        import_repo_into_repo(import_file, current_path)

def open_repo(args):
    global current_path, current_repo
    if current_repo:
        print('Fehler: Bitte verlassen sie zuerst das aktuelle Repo.')
        return
    if not args:
        print('Fehler: Kein Name für das zu öffnende Repo angegeben.')
        return
    repo_name = args[0]
    if not BASE_PATH / repo_name in list_all_repos():
        print('Fehler: Verzeichnis ist kein gültiges BBST-Repo.')
        return
    current_path = BASE_PATH / repo_name
    current_repo = repo_name

def close_repo():
    global current_path, current_repo
    current_path = BASE_PATH
    current_repo = ''

def on_list():
    if current_repo:
        current_repo_list = current_path / TEACHER_LIST_FILENAME
        if not current_repo_list.exists():
            print('Fehler: Aktuelles Repo enthält noch keine Listendatei.')
            return
        table = [astuple(x) for x in read_teacher_list(current_repo_list)]
        headers = list(asdict(Teacher()).keys())
        print(tabulate(table, headers, tablefmt="grid"))
    else:
        print('Verfügbare Repos im Basisverzeichnis:')
        repo_list = list_all_repos()
        if repo_list:
            for r in repo_list:
                print(f'   {r}')
        else:
            print('Keine Repos gefunden!')

def on_add():
    if not current_repo:
        print('Fehler: Hinzufügen von Lehrern nur in Repo möglich.')
        return
    first_name = ''
    last_name = ''
    while not first_name:
        first_name = prompt('Vorname: ').strip()
    while not last_name:
        last_name = prompt('Name: ').strip()
    new_teacher = Teacher(last_name=last_name, first_name=first_name,
                          email=generate_mail_address(last_name), added=True,
                          username=generate_username(first_name, last_name))
    add_new_teacher(new_teacher)

def on_update(args):
    if not current_repo:
        print('Fehler: Aktualisierung ist nur in Repo möglich.')
        return
    if not args:
        print('Fehler: Keine Datei angegeben.')
        return
    update_file = (current_path / args[0]).resolve()
    if not update_file.exists():
        print('Fehler: Zu übernehmende Datendatei existiert nicht.')
        return
    new_teachers, deleted_teachers = read_bbsv_file(update_file)
    for t in new_teachers:
        add_new_teacher(t)
    print('{} neue Lehrer hinzugefügt.'.format(len(new_teachers)))
    for t in deleted_teachers:
        on_delete([t.guid])
        print('Lehrer {} wurde als gelöscht markiert.'.format(t))

def on_import(args):
    if not current_repo:
        print('Fehler: Import nur in Repo möglich.')
        return
    if not args:
        print('Fehler: Kein Dateipfad angegeben.')
        return
    import_repo_name = args[0]
    import_repo = BASE_PATH / import_repo_name
    if not import_repo in list_all_repos():
        print('Fehler: Kein gültiges zu importierendes Repo angegeben.')
        return
    print(f'Importiere Liste aus Repo {import_repo_name}...')
    import_repo_into_repo(import_repo, current_repo)

def on_export():
    if not current_repo:
        print('Fehler: Export ist nur in Repo möglich.')
        return
    print('Exportieren aktuelles Repo in alle Exportformate...')
    current_repo_list = current_path / TEACHER_LIST_FILENAME
    if not current_repo_list.exists():
        print('Fehler: Aktuelles Repo enthält noch keine Listendatei.')
        return
    teacher_list = read_teacher_list(current_repo_list)
    output_file = current_path / USER_INFO_FILENAME
    create_user_info_document(str(output_file), teacher_list)

def on_amend(args):
    if not current_repo:
        print('Fehler: Änderungen sind nur in Repo möglich.')
        return
    if not args:
        print('Fehler: Keine GUID angegeben.')
        return
    current_repo_list = current_path / TEACHER_LIST_FILENAME
    l = read_teacher_list(current_repo_list)
    # find teacher whose GUID starts with given argument
    chosen_teacher = [t for t in l if t.guid.startswith(args[0])]
    if len(chosen_teacher) != 1:
        print('Fehler: Kein oder zu viele Übereinstimmungen gefunden.')
        return
    # ask for changed information
    first_name = prompt('Geben Sie den neuen Vornamen ein: ', default=chosen_teacher[0].first_name)
    last_name = prompt('Geben Sie den neuen Nachnamen ein: ', default=chosen_teacher[0].last_name)
    email = prompt('Geben Sie die neue Email-Adresse ein: ', default=chosen_teacher[0].email)
    username = prompt('Geben Sie den neuen Benutzernamen ein: ', default=chosen_teacher[0].username)
    # remove old teacher and add amended teacher
    l.remove(chosen_teacher[0])
    l.append(Teacher(last_name=last_name, first_name=first_name, email=email, username=username,
                     guid=chosen_teacher[0].guid, password=chosen_teacher[0].password))
    write_teacher_list(l, current_repo_list)

def on_delete(args, purge=False):
    if not current_repo:
        # TODO: Add feature to delete complete Repos.
        print('Fehler: Löschen ist nur in Repo möglich.')
        return
    if not args:
        print('Fehler: Keine GUID angegeben.')
        return
    current_repo_list = current_path / TEACHER_LIST_FILENAME
    l = read_teacher_list(current_repo_list)
    # find teacher whose GUID starts with given argument
    chosen_teacher = [t for t in l if t.guid.startswith(args[0])]
    if len(chosen_teacher) != 1:
        print('Fehler: Kein oder zu viele Übereinstimmungen gefunden.')
        return
    really = prompt('Soll der Lehrer "{}" wirklich gelöscht werden? [y/N] '.format(chosen_teacher[0]))
    if really.lower() == 'y':
        l.remove(chosen_teacher[0])
        if not purge:
            l.append(replace(chosen_teacher[0], deleted=True))
        write_teacher_list(l, current_repo_list)

##################################  CLI  ######################################

def prepare_completers(commands):
    completer_commands = WordCompleter(commands)
    repos = [str(r.parts[-1:][0]) for r in list_all_repos()]
    completer_repos = WordCompleter(repos)
    completer_files = PathCompleter(file_filter=lambda filename: str(filename).endswith('.csv'),
                                    min_input_len=0, get_paths=lambda : [current_path])
    return merge_completers([completer_commands, completer_repos, completer_files])

def prepare_key_bindings():
    bindings = KeyBindings()
    @bindings.add('c-x')
    def _(event):
        " Exit when `c-x` is pressed. "
        event.app.exit()
    return bindings

def prepare_cli_interface(commands):
    style = Style.from_dict({
        # user input (default text)
        '':       '#00ff00',
        # prompt
        'pound':  '#00ff00',
        'path':   'ansicyan',
        # toolbar
        'bottom-toolbar': '#333333 bg:#ffcc00'
    })
    toolbar_text = f' Basisverzeichnis: {BASE_PATH}  -  Zum Beenden Strg+d oder Strg+c drücken.'
    our_history = FileHistory(HISTORY_FILE)
    session = PromptSession(auto_suggest=AutoSuggestFromHistory(), history=our_history, style=style,
                            completer=prepare_completers(commands), key_bindings=prepare_key_bindings(),
                            bottom_toolbar=toolbar_text, complete_while_typing=True)
    return session

@click.command()
@click.option('--verbose', '-v', is_flag=True, help='Enables verbose mode.', default=False)
@click.option('--test', is_flag=True, help='No changes are written to disk.', default=False)
@click.version_option('0.1')
def main_loop(test, verbose):
    "Simple tool for managing user accounts for teachers at a vocational school."

    # TODO: Add command 'amend' to change and 'delete' to remove entry.
    commands = ['new', 'import', 'export', 'open', 'close', 'list', 'add', 'update', 'help', 'exit', 'quit', 'amend', 'delete']
    session = prepare_cli_interface(commands)

    while True:
        if current_repo:
            prompt_message = [ ('class:pound', ' ➭ '),
                               ('class:path', current_repo),
                               ('class:pound', ' ➭ ') ]
        else:
            prompt_message = [ ('class:pound', ' ➭ ') ]
        user_input = session.prompt(prompt_message, completer=prepare_completers(commands))
        if not user_input:
            continue
        else:
            user_input = user_input.split()
        command, args = user_input[0], user_input[1:]
        if command == 'exit' or command == 'quit':
            return
        elif command == 'help':
            # TODO: Add more information on available commands.
            print('Mögliche Befehle: ', ', '.join(commands))
        elif command == 'new':
            create_repo(args)
        elif command == 'open':
            open_repo(args)
        elif command == 'close':
            close_repo()
        elif command == 'list':
            on_list()
        elif command == 'import':
            on_import(args)
        elif command == 'export':
            on_export()
        elif command == 'amend':
            on_amend(args)
        elif command == 'delete':
            on_delete(args)
        elif command == 'add':
            on_add()
        elif command == 'update':
            on_update(args)
        else:
            print('Fehler: Befehl ungültig. Verwenden Sie den Befehl "help" für weitere Informationen.')

def create_logger():
    # create logger for this application
    global logger
    logger.setLevel(logging.DEBUG)
    log_to_file = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=262144,
                                                       backupCount=5, encoding='utf-8')
    log_to_file.setLevel(logging.DEBUG)
    logger.addHandler(log_to_file)
    log_to_screen = logging.StreamHandler(sys.stdout)
    log_to_screen.setLevel(logging.INFO)
    logger.addHandler(log_to_screen)

if __name__ == '__main__':
    create_logger()
    main_loop()
