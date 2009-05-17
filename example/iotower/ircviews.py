from models import *
from django import http
from django.shortcuts import get_object_or_404
from yardbird import IRCResponse


def learn(request, key='', verb='is', value='', **kwargs):
    if 'addressee' not in kwargs or kwargs['addressee'] != request.nick:
        raise Exception, 'You must address me to perform this operation.'
    factoid, created = Factoid.objects.get_or_create(fact=key.lower())
    if not created and factoid.protected:
        raise Exception, 'That factoid is protected!'
    else:
        factext = FactoidResponse(fact=factoid, verb=verb, text=value)
        factext.save()
    nick = request.user.split('!', 1)[0]
    if request.channel != request.nick:
        recipient = request.channel
    else:
        recipient = nick
    return IRCResponse(recipient, u'OK, %s.' % nick)

def trigger(request, key='', verb='', **kwargs):
    factoid = get_object_or_404(Factoid, fact__iexact=key)
    try:
        text = factoid.factoidresponse_set.filter(
            verb__contains=verb).order_by("?")[0]
    except IndexError:
        #FIXME: this is just for testing
        text = factoid.factoidresponse_set.order_by("?")[0]
    nick = request.user.split('!', 1)[0]
    if request.channel != request.nick:
        recipient = request.channel
    else:
        recipient = nick
    return IRCResponse(recipient, u'%s: %s =%s= %s' % (nick,
                                                     key, text.verb,
                                                     text.text))




