
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
    fieldnames = ['guid', 'email', 'short_name', 'last_name', 'first_name', 'classes',
                  'courses', 'birthday', 'initial_password', 'deleted', 'new',
                  'teacher','groups']
    with open(update_file, 'r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';', fieldnames=fieldnames)
        for i, row in enumerate(reader):
            guid = row['guid'].replace('{','').replace('}','')
            #email = row['email']
            #short_name = row['short_name']
            last_name = row['last_name']
            first_name = row['first_name']
            #classes = row['classes']
            #courses = row['courses']
            #birthday = row['birthday']
            #initial_password = row['initial_password]
            was_deleted = row['deleted']             # deleted = -1 / else = 0
            is_new_user = row['new']                 # new = -1 / else = 0
            #is_teacher_or_student = row['teacher']  # teacher = -1 / student = 0
            #group_memberships = row['groups']
            new_teacher = Teacher(guid=guid, last_name=last_name, first_name=first_name,
                                  email=generate_mail_address(last_name),
                                  username=generate_username(first_name, last_name))
            if was_deleted == '-1':
                deleted_teachers.append(new_teacher)
            if is_new_user == '-1':
                new_teachers.append(new_teacher)
        else:
            print('{} Lehrer aus Datei eingelesen.'.format(i+1))
    return new_teachers, deleted_teachers

def read_teacher_list(file_name):
    teachers_list = []
    with open(file_name, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            new_teacher = Teacher(**row)
            teachers_list.append(new_teacher)
    return teachers_list

def write_teacher_list(teacher_list, file_name):
    fieldnames = list(asdict(Teacher()).keys())
    with open(file_name, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for t in teacher_list:
            writer.writerow(asdict(t))
