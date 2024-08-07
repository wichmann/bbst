
import uuid
import random
import logging
from dataclasses import dataclass, field

logger = logging.getLogger('bbst.data')


PASSWORD_LENGTH = 10


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
            ' ': '',
            'š': 's'}


def replace_illegal_characters(string):
    """Replaces illegal characters from a given string with values from char map."""
    characters = list(string)
    return ''.join([char_map[char] if char in char_map else char for char in characters])

def generate_username(first_name, last_name):
    return 'KOL.{}{}'.format(replace_illegal_characters(last_name)[0:4].upper(),
                             replace_illegal_characters(first_name)[0:4].upper())

def generate_mail_address(last_name):
    return '{}@bbs-brinkstrasse.de'.format(replace_illegal_characters(last_name).lower())

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
    specialchars = '!?%&-+*'
    chars = uppercase + lowercase + digits
    # fill up with at least one uppercase, one lowercase, one digit and one special character
    password += random.SystemRandom().choice(uppercase)
    password += random.SystemRandom().choice(lowercase)
    password += random.SystemRandom().choice(digits)
    password += random.SystemRandom().choice(specialchars)
    # fill password up with more characters
    password += [random.SystemRandom().choice(chars) for _ in range(PASSWORD_LENGTH-4)]
    # shuffle characters of password string
    random.shuffle(password)
    logger.debug('New password generated: ' + ''.join(password))
    return ''.join(password)

@dataclass() #frozen=True
class Teacher:
    guid: str = field(default_factory=uuid.uuid4)
    last_name: str = field(default='', compare=False)
    first_name: str = field(default='', compare=False)
    email: str = field(default='', compare=False)
    username: str = field(default='', compare=False)
    password: str = field(default_factory=generate_good_readable_password, compare=False)
    # signals that teacher was added after initial import into Repo, either by the add or update command
    added: bool = field(default=False, compare=False, repr=False)
    # signals that teacher was deleted after initial import into Repo by the delete command
    deleted: bool = field(default=False, compare=False, repr=False)

    def __str__(self):
        return '<{} {}>'.format(self.first_name, self.last_name)
