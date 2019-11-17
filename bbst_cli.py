#! /usr/bin/env python3

"""
bbst - BBS Teacher Management

@author: Christian Wichmann
"""

import shutil
import logging
from pathlib import Path
from datetime import datetime
from dataclasses import asdict, astuple

import click
from tabulate import tabulate
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.completion import Completer, Completion, WordCompleter, PathCompleter, merge_completers
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.application import run_in_terminal
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.shortcuts import message_dialog, yes_no_dialog, input_dialog, ProgressBar
from prompt_toolkit.history import FileHistory

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus.flowables import Image, PageBreak

from bbst.data import Teacher, generate_mail_address, generate_username
from bbst.fileops import read_bbsv_file, read_teacher_list, write_teacher_list


logger = logging.getLogger('bbst')


REPO_TOKEN = '.bbst'
TEACHER_LIST_FILENAME = 'teacher_list.csv'


base_path = Path().cwd()
current_path = base_path
current_repo = ''


####################################  Handler ##############################################

def create_new_repo(args):
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
    if not base_path / repo_name in list_all_repos():
        print('Fehler: Verzeichnis ist kein gültiges BBST-Repo.')
        return
    current_path = base_path / repo_name
    current_repo = repo_name

def close_repo():
    global current_path, current_repo
    current_path = base_path
    current_repo = ''

def import_repo_into_repo(import_repo, destination_repo):
    """
    Reads a given import file in CSV format and copies it into a given directory.
    """
    # TODO: Expand function to import user from file if teachers list already exists
    destination_file = base_path / destination_repo / TEACHER_LIST_FILENAME
    source_file = base_path / import_repo / TEACHER_LIST_FILENAME
    if destination_file.exists():
        print('Fehler: Liste existiert bereits in angegebenen Repo.')
        return
    shutil.copy(source_file, destination_file)

def list_all_repos():
    return [d for d in base_path.iterdir() if d.is_dir() and (d/REPO_TOKEN).exists()]

def on_list_command():
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

def on_add_command(session):
    if not current_repo:
        print('Fehler: Hinzufügen von Lehrern nur in Repo möglich.')
        return
    first_name = session.prompt('Vorname: ')
    last_name = session.prompt('Name: ')
    new_teacher = Teacher(last_name=last_name, first_name=first_name,
                          email=generate_mail_address(last_name),
                          username=generate_username(first_name, last_name))
    add_new_teacher(new_teacher)

def add_new_teacher(new_teacher):
    current_repo_list = current_path / TEACHER_LIST_FILENAME
    l = read_teacher_list(current_repo_list)
    l.append(new_teacher)
    write_teacher_list(l, current_repo_list)

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
        print('Lehrer {} sollte gelöscht werden.'.format(t))

def on_import_command(args):
    if not current_repo:
        print('Fehler: Import nur in Repo möglich.')
        return
    if not args:
        print('Fehler: Kein Dateipfad angegeben.')
        return
    import_repo_name = args[0]
    import_repo = Path().cwd() / import_repo_name
    if not import_repo in list_all_repos():
        print('Fehler: Kein gültiges zu importierendes Repo angegeben.')
        return
    print(f'Importiere Liste aus Repo {import_repo_name}...')
    #result = yes_no_dialog(title='Import durchführen?',
    #                       text=f'Wirklich die Datei {import_repo} in aktuelles Repo importieren?')
    #if result:
    #    with ProgressBar() as pb:  
    #        for i in pb(range(800)):
    #            pass
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
    output_file = current_path / 'Anschreiben.pdf'
    create_user_info_document(str(output_file), teacher_list)

PAGE_WIDTH, PAGE_HEIGHT = A4
BORDER_HORIZONTAL = 2.0*cm
BORDER_VERTICAL = 1.5*cm

def build_footer(canvas, doc):
    today = datetime.today().strftime('%d.%m.%Y')
    canvas.saveState()
    canvas.setFont('Helvetica', 10)
    canvas.drawString(BORDER_HORIZONTAL, BORDER_VERTICAL, today)
    canvas.drawRightString(PAGE_WIDTH-BORDER_HORIZONTAL, BORDER_VERTICAL, "Seite {}".format(doc.page))
    canvas.restoreState()

def create_user_info_document(output_file, teacher_list):
    logger.debug('Creating user info document...')
    subject_paragraph_style = ParagraphStyle(name='Normal', fontSize=12, leading=18, fontName='Times-Bold', spaceAfter=0.75*cm)
    main_paragraph_style = ParagraphStyle(name='Normal', fontSize=11, leading=18, fontName='Times-Roman', spaceAfter=0.25*cm)
    data_paragraph_style = ParagraphStyle(name='Normal', fontSize=12, fontName='Courier', spaceAfter=0.5*cm, alignment=TA_CENTER)
    # prepare data for document
    title = 'Benutzerdaten'
    author = 'bbst - BBS Teacher Management'
    logo = Image('logo.png', width=PAGE_WIDTH-2*BORDER_HORIZONTAL, height=5.2445*cm)
    logo.hAlign = 'CENTER'
    info_text_1 = 'Liebe Kollegin, lieber Kollege,<br/><br/>ihre Benutzerdaten lauten wie folgt:'
    info_text_2 = """Diese Zugangsdaten erlauben die Rechnernutzung in allen Räumen mit dem Logodidact-System.
    Außerdem kann es zum Zugriff auf den Stundenplan über WebUntis und die Lern­plattform Moodle genutzt werden.<br/>
    In Logodidact, Moodle und WebUntis lässt sich das Passwort ändern. Allerdings gilt jede Änderung nur für
    das jeweilige System! Sollten Sie ihr Passwort vergessen haben, besteht bei Moodle und Webuntis die
    Möglichkeit, sich ein neues Passwort per Mail zusenden zu lassen.<br/>
    Weitere Informationen finden Sie im Moodle-Kurs: <a>https://moodle.nibis.de/bbs_osb/course/view.php?id=7</a>.
    Bei allen weiteren Fragen können Sie sich gerne bei mir melden.<br/><br/>
    Viele Grüße<br/>&nbsp;&nbsp;&nbsp;&nbsp;Christian Wichmann<br/>&nbsp;&nbsp;&nbsp;&nbsp;wichmann@bbs-os-brinkstr.de"""
    # building document
    doc = SimpleDocTemplate(output_file, author=author, title=title)
    story = []
    for t in teacher_list:
        user_data = '{}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{}'.format(t.username, t.password)
        #story.append(logo)
        story.append(Spacer(1,1.75*cm))
        story.append(Paragraph('<b>{}</b>'.format(title), subject_paragraph_style))
        story.append(Paragraph(info_text_1, main_paragraph_style))
        story.append(Paragraph(user_data, data_paragraph_style))
        story.append(Paragraph(info_text_2, main_paragraph_style))
        story.append(PageBreak())
    doc.build(story, onFirstPage=build_footer, onLaterPages=build_footer)

def prepare_completers(commands):
    completer_commands = WordCompleter(commands)
    repos = [str(r.parts[-1:][0]) for r in list_all_repos()]
    completer_repos = WordCompleter(repos)
    def filter_csv(filename):
        return str(filename).endswith('.csv')
    def paths_for_completion():
        return [current_path.cwd()]
    completer_files = PathCompleter(file_filter=filter_csv, min_input_len=2, get_paths=paths_for_completion)
    return merge_completers([completer_files, completer_commands, completer_repos])

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
    toolbar_text = f' Basisverzeichnis: {base_path}  -  Zum Beenden Strg+d oder Strg+c drücken.'
    our_history = FileHistory('.bbst-history-file')
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

    global base_path, current_path, current_repo

    # TODO: Add command 'amend' to change entry.
    commands = ['new', 'import', 'export', 'open', 'close', 'list', 'add', 'update', 'help', 'exit', 'quit']
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
            print('Mögliche Befehle: ', ', '.join(commands))
        elif command == 'new':
            create_new_repo(args)
        elif command == 'open':
            open_repo(args)
        elif command == 'close':
            close_repo()
        elif command == 'list':
            on_list_command()
        elif command == 'import':
            on_import_command(args)
        elif command == 'export':
            on_export()
        elif command == 'add':
            on_add_command(session)
        elif command == 'update':
            on_update(args)
        else:
            print('Fehler: Befehl ungültig. Mögliche Befehle: ', ', '.join(commands))

if __name__ == '__main__':
    main_loop(False, False)
