#!/usr/bin/python
from django.conf import settings
from django.utils.encoding import force_unicode, DjangoUnicodeDecodeError

def unicode_fallback(msg, encodings=settings.IRC_INPUT_ENCODINGS):
    """Attempt to decode message into unicode, using the given encodings.
    Defaults to the value of settings.IRC_INPUT_ENCODINGS. or utf-8, then
    CP1252 if settings.IRC_INPUT_ENCODINGS. is not set."""
    if settings.IRC_INPUT_ENCODINGS == None:
        encodings = ['utf_8', 'cp1252']
    for encoding in encodings:
        try:
            return force_unicode(msg, encoding)
        except DjangoUnicodeDecodeError as e:
            last_exception = e
    raise last_exception
