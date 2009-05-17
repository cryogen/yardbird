from models import *
from django import http
from django.shortcuts import get_object_or_404
from yardbird import IRCResponse

def reply(request, text, *args):
    if request.channel != request.user_nick:
        recipient = request.channel
    else:
        recipient = request.user_nick
    return IRCResponse(recipient, text % args)

def require_addressing(function):
    def new(request, *args, **kwargs):
        if 'addressee' not in kwargs or kwargs['addressee'] != request.nick:
            raise Exception, 'You must address me to perform this operation.'
        return function(request, *args, **kwargs)
    return new

@require_addressing
def learn(request, key='', verb='is', value='', **kwargs):
    factoid, created = Factoid.objects.get_or_create(fact=key.lower())
    if not created and factoid.protected:
        raise Exception, 'That factoid is protected!'
    else:
        factext = FactoidResponse(fact=factoid, verb=verb, text=value,
                                  created_by=request.user_nick)
        factext.save()
    return reply(request, u'OK, %s.', request.user_nick)

def trigger(request, key='', verb='', **kwargs):
    factoid = get_object_or_404(Factoid, fact__iexact=key)
    try:
        text = factoid.factoidresponse_set.filter(
            verb__contains=verb).order_by("?")[0]
    except IndexError:
        #FIXME: this is just for testing
        text = factoid.factoidresponse_set.order_by("?")[0]
    return reply(request, u'%s: %s =%s= %s', request.user_nick, key,
                                              text.verb, text.text)

@require_addressing
def literal(request, key='', **kwargs):
    factoid = get_object_or_404(Factoid, fact__iexact=key)
    responses = factoid.factoidresponse_set.filter(disabled__exact=None)
    return reply(request, unicode(responses.order_by('created')))

