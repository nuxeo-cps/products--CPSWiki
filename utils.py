# -*- coding: ISO-8859-15 -*-
# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
# Author: Tarek Ziad� <tz@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$
import string
from datetime import datetime
from random import randrange
import re

# a few methods ripped
# for quick integration
# we assume that we will add dependencies
# later

_translation_table = string.maketrans(
    # XXX candidates: @�+=`|
    '"' r"""'/\:; &�������������������������������������������������������""",
    '_' r"""_______AAAAAACEEEEIIIINOOOOOOUUUUYaaaaaaceeeeiiiinoooooouuuuyy""")

_ok_chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_."


def makeId(s, lower=0):
    "Make id from string"
    id = s.translate(_translation_table)
    id = id.replace('�', 'AE')
    id = id.replace('�', 'ae')
    id = id.replace('�', 'OE')
    id = id.replace('�', 'oe')
    id = id.replace('�', 'ss')
    id = ''.join([c for c in id if c in _ok_chars])
    id = re.sub('_+', '_', id)
    while id.startswith('_') or id.startswith('.'):
        id = id[1:]
    while id.endswith('_'):
        id = id[:-1]
    if not id:
        # Fallback if empty or incorrect
        newid = str(int(datetime())) + str(randrange(1000, 10000))
        return newid
    if lower:
        id = id.lower()
    return id

def getCurrentDateStr():
    """ gets current date
    """
    date = datetime(1970, 1, 1)
    now = date.now()
    # english style
    return now.strftime('%a %m/%d/%y %H:%M')
