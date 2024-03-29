#!/usr/bin/python
from django.conf import settings
from django.utils.encoding import force_unicode as django_force_unicode
from django.utils.encoding import DjangoUnicodeDecodeError

def force_unicode(msg, encodings=None):
    """Attempt to decode message into unicode, using the given encodings.
    Defaults to the value of settings.IRC_INPUT_ENCODINGS. or utf-8, then
    CP1252 if settings.IRC_INPUT_ENCODINGS. is not set."""

    # Use a default if the settings is not set
    if not encodings:
        encodings = getattr(settings, 'IRC_INPUT_ENCODINGS',
                ['utf_8', 'cp1252'])
            
    if not encodings:
        raise ValueError("No input encodings specified")

    for encoding in encodings:
        try:
            return django_force_unicode(msg, encoding)
        except DjangoUnicodeDecodeError as e:
            last_exception = e
    # If we haven't returned, raise the last exception (giving up)
    raise last_exception
