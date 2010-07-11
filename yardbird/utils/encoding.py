#!/usr/bin/python
from django.conf import settings
from django.utils.encoding import force_unicode, DjangoUnicodeDecodeError

def unicode_fallback(msg):
    """Attempt to decode message into unicode, using encodings defined in
    settings.IRC_INPUT_ENCODINGS.  Defaults to utf-8, then cp1252"""
    input_encodings = ['utf_8', 'cp1252']
    if settings.IRC_INPUT_ENCODINGS:
        input_encodings = settings.IRC_INPUT_ENCODINGS
    for encoding in input_encodings:
        try:
            return force_unicode(msg, encoding)
        except DjangoUnicodeDecodeError as e:
            last_exception = e
    raise last_exception
