VERSION = 'Another Hairdo'
TARGET = '0.9'

def sdist_ver():
    import re
    if VERSION == TARGET:
        return VERSION
    codename = re.sub(r'\W', '.', VERSION)
    return '%s~%s' % ( TARGET, codename )
