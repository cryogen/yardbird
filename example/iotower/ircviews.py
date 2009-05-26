import re

from models import *
from django import http
from django.shortcuts import get_object_or_404
from django.conf import settings
from yardbird import IRCResponse

def reply(request, text, *args):
    if request.channel != request.nick:
        recipient = request.channel
    else:
        recipient = request.user_nick
    return IRCResponse(recipient, text % args)

def addressed(request, *args, **kwargs):
    if request.channel == request.nick:
        return True
    elif 'addressee' in kwargs and kwargs['addressee'] == request.nick:
        return True
    return False

def require_addressing(function):
    def new(request, *args, **kwargs):
        if addressed(request, **kwargs):
            return function(request, *args, **kwargs)
        raise Exception, 'You must address me to perform this operation.'
    return new

def require_chanop(function):
    def new(request, *args, **kwargs):
        chan = settings.IRC_PRIVILEGED_CHANNEL
        if '@' in request.chanmodes[chan][request.user]:
            return function(request, *args, **kwargs)
        raise Exception, 'You lack the necessary privileges to use this command.'
    return new

#@require_addressing
def learn(request, key='', verb='is', value='', **kwargs):
    factoid, created = Factoid.objects.get_or_create(fact=key.lower())
    if not created and factoid.protected:
        raise Exception, 'That factoid is protected!'
    elif 'also' in kwargs:
        factext = FactoidResponse(fact=factoid, verb=verb, text=value,
                                  created_by=request.user_nick)
        factext.save()
    else:
        return reply(request, u'Sorry, %s.', request.user_nick)
    return reply(request, u'OK, %s.', request.user_nick)

def trigger(request, key='', verb='', **kwargs):
    # Only be noisy about unknown factoids if addressed.
    if addressed(request, **kwargs):
        factoid = get_object_or_404(Factoid, fact__iexact=key)
    else:
        try:
            factoid = Factoid.objects.get(fact__iexact=key)
        except:
            return IRCResponse('', '', 'QUIET')
    try:
        text = factoid.factoidresponse_set.filter(
            verb__contains=verb,disabled__exact=None).order_by("?")[0]
    except IndexError:
        #FIXME: this is just for testing
        text = factoid.factoidresponse_set.order_by("?")[0]
    return reply(request, u'%s: %s %s %s', request.user_nick, key,
                                              text.verb, text.text)

@require_addressing
@require_chanop
def literal(request, key='', **kwargs):
    factoid = get_object_or_404(Factoid, fact__iexact=key)
    responses = factoid.factoidresponse_set.filter(disabled__exact=None)
    text = key
    verb = ''
    for response in responses.order_by('verb'):
        if response.verb != verb:
            verb = response.verb
            text += ' =%s= ' % verb
        else:
            text += '|'
        text += '%s' % response.text

    return reply(request, unicode(text))

@require_addressing
def edit(request, key='', pattern='', replacement='', re_flags='', **kwargs):
    flags = re.UNICODE
    count = 1
    if 'i' in re_flags:
        flags |= re.IGNORECASE
    if 'g' in re_flags:
        count = 0
    pat = re.compile(pattern, flags)
    factoid = get_object_or_404(Factoid, fact__iexact=key)
    responses = factoid.factoidresponse_set.filter(disabled__exact=None)
    for response in responses:
        if pat.search(response.text):
            newtext = pat.sub(replacement, response.text, count)
            edited = FactoidResponse(fact=factoid, verb=response.verb,
                                     text=newtext,
                                     created_by=request.user_nick)
            edited.save() # To generate creation time.
            response.disabled = edited.created
            response.disabled_by = edited.created_by
            response.save()
            return reply(request, u'%s: %s =%s= %s', request.user_nick,
                         key, edited.verb, edited.text)
    raise Exception, 'No response in %s contained your pattern' % key



