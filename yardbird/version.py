VERSION = 'Anthropology'
TARGET = '0.9'

def sdist_ver(): #pragma: nocover
    import re
    if VERSION == TARGET:
        return VERSION
    codename = re.sub(r'\W', '.', VERSION)
    return '%s~%s' % ( TARGET, codename )
