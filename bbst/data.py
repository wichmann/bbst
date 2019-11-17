
import uuid
import random
import logging
from dataclasses import dataclass


logger = logging.getLogger('bbst.data')


PASSWORD_LENGTH = 8


### map translating all illegal characters into legal (ascii) characters
char_map = {'ä': 'ae',
            'à': 'a',
            'á': 'a',
            'â': 'a',
            'ã': 'a',
            'Ä': 'Ae',
            'À': 'A',
            'Á': 'A',
            'Â': 'A',
            'Ã': 'A',
            'è': 'e',
            'é': 'e',
            'ê': 'e',
            'È': 'E',
            'É': 'E',
            'Ê': 'E',
            'ö': 'oe',
            'ò': 'o',
            'ó': 'o',
            'ô': 'o',
            'õ': 'o',
            'Ö': 'Oe',
            'Ò': 'O',
            'Ó': 'O',
            'Ô': 'O',
            'Õ': 'O',
            'ü': 'ue',
            'ù': 'u',
            'ú': 'u',
            'û': 'u',
            'Ü': 'Ue',
            'Ù': 'U',
            'Ú': 'U',
            'Û': 'U',
            'í': 'i',
            'ß': 'ss',
            'Ç': 'C',
            'ç': 'c',
            'č': 'c',
            'ć': 'c',
            '´': '',
            '-': '',
            ' ': ''}


def replace_illegal_characters(string):
    """Replaces illegal characters from a given string with values from char map."""
    characters = list(string)
    return ''.join([char_map[char] if char in char_map else char for char in characters])

def generate_username(first_name, last_name):
    return 'KOL.{}{}'.format(replace_illegal_characters(last_name)[0:4].upper(),
                             replace_illegal_characters(first_name)[0:4].upper())

def generate_mail_address(last_name):
    return '{}@bbs-os-brinkstr.de'.format(last_name.lower())

def generate_good_readable_password():
    """
    Generate a random password for a given length including all letters and
    digits. This password contains at least one lower case letter, one upper
    case letter and one digit. To generate unpredictable passwords, the
    SystemRandom class from the random module is used! All ambiguous characters
    are exempt from passwords.

    Source: https://stackoverflow.com/questions/55556/characters-to-avoid-in-automatically-generated-passwords
   
    :return: string containing random password of good quality
    """
    password = []
    # define possible characters for use in passwords (source: https://www.grc.com/ppp.htm)
    uppercase = 'ABCDEFGHJKLMNPRSTUVWXYZ'
    lowercase = 'abcdefghijkmnopqrstuvwxyz'
    digits = '23456789'
    chars = uppercase + lowercase + digits
    # fill up with at least one uppercase, one lowercase and one digit
    password += random.SystemRandom().choice(uppercase)
    password += random.SystemRandom().choice(lowercase)
    password += random.SystemRandom().choice(digits)
    # fill password up with more characters
    password += [random.SystemRandom().choice(chars) for _ in range(PASSWORD_LENGTH-3)]
    # shuffle characters of password string
    random.shuffle(password)
    logger.debug('New password generated: ' + ''.join(password))
    return ''.join(password)


@dataclass(frozen=True)
class Teacher:
    guid: str = uuid.uuid4()
    last_name: str = ''
    first_name: str = ''
    email: str = ''
    username: str = ''
    password: str = generate_good_readable_password()
