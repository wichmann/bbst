
import os
import csv
import logging
from dataclasses import asdict

from bbst.data import Teacher, generate_mail_address, generate_username, generate_good_readable_password


logger = logging.getLogger('bbst.fileops')


def read_bbsv_file(update_file):
    """
    Reads a teachers list exported by BBS Verwaltung. Two lists containing all
    new and deleted teachers will be returned.
    """
    deleted_teachers = []
    new_teachers = []
    all_teachers = []
    fieldnames = ['guid', 'email', 'short_name', 'last_name', 'first_name', 'classes',
                  'courses', 'birthday', 'initial_password', 'deleted', 'new',
                  'teacher','groups']
    with open(update_file, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', fieldnames=fieldnames)
        for i, row in enumerate(reader):
            guid = row['guid'].replace('{','').replace('}','').lower()
            #email = row['email']
            #short_name = row['short_name']
            last_name = row['last_name']
            first_name = row['first_name']
            #classes = row['classes']
            #courses = row['courses']
            #birthday = row['birthday']
            #initial_password = row['initial_password]
            was_deleted = row['deleted'] == '-1'     # deleted = -1 / else = 0
            is_new_user = row['new'] == '-1'         # new = -1 / else = 0
            #is_teacher_or_student = row['teacher']  # teacher = -1 / student = 0
            #group_memberships = row['groups']
            new_teacher = Teacher(guid=guid, last_name=last_name, first_name=first_name,
                                  email=generate_mail_address(last_name),
                                  username=generate_username(first_name, last_name),
                                  added=is_new_user, deleted=was_deleted)
            if was_deleted:
                deleted_teachers.append(new_teacher)
            if is_new_user:
                new_teachers.append(new_teacher)
            all_teachers.append(new_teacher)
        else:
            print('{} Lehrer aus Datei eingelesen.'.format(i+1))
    return new_teachers, deleted_teachers, all_teachers

def read_teacher_list(file_name):
    teachers_list = []
    with open(file_name, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # parse strings from CSV file for boolean values
            row['added'] = True if row['added'] == 'True' else False
            row['deleted'] = True if row['deleted'] == 'True' else False
            # unify guid representation
            row['guid'] = row['guid'].replace('{','').replace('}','').lower()
            new_teacher = Teacher(**row)
            teachers_list.append(new_teacher)
    return teachers_list

def write_teacher_list(teacher_list, file_name):
    fieldnames = list(asdict(Teacher()).keys())
    with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for t in teacher_list:
            writer.writerow(asdict(t))


def write_moodle_file(teacher_list, output_file='Moodle.csv'):
    """
    Writes a file containing all added and deleted teachers to be imported into Moodle.
    
    :param teacher_list: list of teachers
    :param output_file: file name to write student list to
    
    File format for importing users into Moodle:
    cohort1;    lastname;   firstname;  username;       password;   email;                  sysrole1;       deleted
    Kollegium;  Müller;     Kirsten;    kol.muelkirs;   12345678;   mueller@example.com;    coursecreator;  0 
    """
    if os.path.exists(output_file):
        logger.warn('Moodle-Datei existiert schon und wird überschrieben!')
    # export file with all changed teachers
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        count = 0
        output_file_writer = csv.writer(csvfile, delimiter=';')
        output_file_writer.writerow(('cohort1', 'lastname', 'firstname', 'username',
                                     'password', 'email', 'sysrole1', 'deleted'))
        for teacher in teacher_list:
            if teacher.added or teacher.deleted:
                output_file_writer.writerow(('Kollegium', teacher.last_name, teacher.first_name, teacher.username.lower(),
                                             teacher.password, teacher.email, 'coursecreator', '1' if teacher.deleted else '0'))
                count += 1
        logger.debug('{0} teachers exported to Moodle file format.'.format(count))

def write_radius_file(teacher_list, output_file='Radius.csv'):
    if os.path.exists(output_file):
        logger.warn('Output file already exists, will be overwritten...')
    with open(output_file, 'w', encoding='utf-8') as export_file:
        count = 0
        line = '{:20}\t\tCleartext-Password := "{}"\n'
        for teacher in teacher_list:
            if teacher.added:
                count += 1
                formatted_line = line.format(teacher.username.lower(), teacher.password)
                export_file.write(formatted_line)
        logger.debug('{0} teacher exported to radius file format.'.format(count))

def write_webuntis_file(teacher_list, output_file='Webuntis.csv'):
    if os.path.exists(output_file):
        logger.warn('Output file already exists, will be overwritten...')
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        output_file_writer = csv.writer(csvfile, delimiter=';')
        # do not output header because otherwise Webuntis creates a user names "Benutzername" ;-)
        #output_file_writer.writerow(('Name', 'Vorname', 'Benutzernamen', 'Passwort', 'Personenrolle', 'Benutzergruppe', 'Email'))
        for teacher in teacher_list:
            if teacher.added:
                output_file_writer.writerow((teacher.last_name, teacher.first_name, teacher.username.lower(), teacher.password, 'Personenrolle', 'Benutzergruppe', teacher.email))
            if teacher.deleted:
                print('Bitte folgenden Lehrer manuell in Webuntis löschen: {}'.format(teacher))


def write_logodidact_file(teacher_list, output_file='Logodidact.csv'):
    DEFAULT_OU = 'ou=KOL,ou=KOL,ou=Kollegium,ou=Lehrer,ou=BBSBS,DC=SN,DC=BBSBS,DC=LOCAL'
    if os.path.exists(output_file):
        logger.warn('Output file already exists, will be overwritten...')
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        output_file_writer = csv.writer(csvfile, delimiter=';')
        output_file_writer.writerow(('Klasse', 'Name', 'Firstname', 'UserID', 'Password', 'OU', 'Email'))
        for t in teacher_list:
            if not t.deleted:
                output_file_writer.writerow(('KOL', t.last_name, t.first_name, t.username,
                                             t.password, DEFAULT_OU, t.email))


def write_nbc_file(teacher_list, output_file='NBC.csv'):
    """
    Writes a CSV file containing all added teachers for import into the
    NBC (Niedersächsische Bildungscloud).
    """
    if os.path.exists(output_file):
        logger.warn('Output file already exists, will be overwritten...')
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        output_file_writer = csv.writer(csvfile, delimiter=',')
        output_file_writer.writerow(('firstName', 'lastName', 'email', 'birthday', 'class'))
        for t in teacher_list:
            if t.added:
                output_file_writer.writerow((t.first_name, t.last_name, t.email, '', ''))
