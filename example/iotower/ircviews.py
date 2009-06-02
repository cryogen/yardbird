import re

from models import *
from django import http
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.template import Template, Context
from yardbird import IRCResponse, render_to_response, render_to_reply
from yardbird import render_silence, render_error, render_quick_reply

def require_addressing(function):
    def new(request, *args, **kwargs):
        if 'addressee' in kwargs:
            if kwargs['addressee'] == request.my_nick:
                request.addressed = True
        if request.addressed:
            return function(request, *args, **kwargs)
        return render_error(request,
                'You must address me to perform this operation.')
    return new

def require_chanop(function):
    def new(request, *args, **kwargs):
        chan = settings.IRC_PRIVILEGED_CHANNEL
        if request.user in request.chanmodes[chan]:
            if '@' in request.chanmodes[chan][request.user]:
                return function(request, *args, **kwargs)
        return render_error(request,
                'You lack the necessary privileges to use this command.')
    return new

#@require_addressing
def learn(request, key='', verb='is', value='', also='', **kwargs):
    factoid, created = Factoid.objects.get_or_create(fact=key.lower())
    if not created and factoid.protected:
        raise Exception, 'That factoid is protected!'
    elif also or created:
        factext = FactoidResponse(fact=factoid, verb=verb, text=value,
                                  created_by=request.nick)
        factext.save()
        return render_quick_reply(request, "ack.irc")
    return render_quick_reply(request, "sorry.irc")

def trigger(request, key='', verb='', **kwargs):
    # Only be noisy about unknown factoids if addressed.
    if request.addressed:
        factoid = get_object_or_404(Factoid, fact__iexact=key)
        addressee = request.nick
    else:
        try:
            factoid = Factoid.objects.get(fact__iexact=key)
            addressee = ''
        except:
            return render_silence()
    try:
        text = factoid.factoidresponse_set.filter(
            verb__contains=verb,disabled__exact=None).order_by("?")[0]
    except IndexError:
        #FIXME: this is just for testing
        text = factoid.factoidresponse_set.order_by("?")[0]
    context = Context(request.__dict__)
    rendered = Template(text.text).render(context)
    return render_to_reply(request, 'factoid.irc',
                           {'factoid': key, 'verb': text.verb,
                            'text': rendered, 'addressee': addressee})

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

    return IRCResponse(request.reply_recipient, unicode(text))

@require_addressing
def edit(request, key='', pattern='', replacement='', re_flags='',
         addressee='', **kwargs):
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
                                     created_by=request.nick)
            edited.save() # To generate creation time.
            response.disabled = edited.created
            response.disabled_by = edited.created_by
            response.save()
            return render_to_reply(request, 'factoid.irc',
                                   {'factoid': key, 'verb': edited.verb,
                                    'text': edited.text,
                                    'addressee': addressee})
    return render_error(request,
                        'No response in %s contained your pattern' % key)



