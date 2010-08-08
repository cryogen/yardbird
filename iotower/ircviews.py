import re
from datetime import datetime

from models import *
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.template import Template, Context
from django.db.models import Q
from django.core import exceptions
from yardbird.irc import IRCResponse
from yardbird.shortcuts import render_to_response, render_to_reply
from yardbird.shortcuts import render_silence, render_error, render_quick_reply
from yardbird.utils.decorators import require_addressing, require_chanop

@require_addressing
@require_chanop
def reimport(request, *args, **kwargs):
    return IRCResponse(request.reply_recipient, 'Reload successful.',
                       method='RESET')

@require_addressing
@require_chanop
def lock(request, key='', **kwargs):
    factoid, created = Factoid.objects.get_or_create(fact=normalize_factoid_key(key))
    factoid.protected = True
    factoid.save()
    return render_quick_reply(request, "ack.irc")

@require_addressing
@require_chanop
def unlock(request, key='', **kwargs):
    factoid = get_object_or_404(Factoid, fact__iexact=normalize_factoid_key(key))
    factoid.protected = False
    factoid.save()
    return render_quick_reply(request, "ack.irc")

#@require_addressing
def learn(request, key='', verb='is', value='', also='', tag='', **kwargs):
    """Add a factoid record to the database."""
    factoid, created = Factoid.objects.get_or_create(
            fact=normalize_factoid_key(key))
    if factoid.protected:
        raise(exceptions.PermissionDenied, 'That factoid is protected!')
    elif also or created:
        if tag:
            tag = tag.strip().strip('<>')
        factext, created = FactoidResponse.objects.get_or_create(
                fact=factoid, verb=verb, text=value, tag=tag,
                created_by=request.nick)
        if request.addressed:
            if created:
                return render_quick_reply(request, "ack.irc")
            return render_quick_reply(request, "already.irc")
    else:
        num_responses = FactoidResponse.objects.filter(fact=factoid,
                verb=verb, text=value, tag=tag).count()
        if num_responses:
            return render_quick_reply(request, "already.irc")

    # If we got this far, it's worth trying to see if this is just a
    # factoid with 'is' or 'are' in the key.
    try:
        return trigger(request,
                key=request.message.split(':')[-1].strip())
    except Http404, OverflowError:
        # FIXME: This should be an edit conflict exception
        raise(exceptions.PermissionDenied, 'That factoid already exists!')

def trigger(request, key='', verb='', **kwargs):
    """Retrieve a factoid record from the database."""
    factoid = get_object_or_404(Factoid,
            fact__iexact=normalize_factoid_key(key))
    try:
        text = factoid.factoidresponse_set.filter(
            verb__contains=verb,disabled__exact=None).order_by("?")[0]
    except IndexError:
        # If it can't find the verb you asked for, it'll try anything.
        try:
            text = factoid.factoidresponse_set.filter(
                disabled__exact=None).order_by("?")[0]
        except IndexError:
            raise Http404
    if not text.tag:
        template = 'factoid.irc'
    else:
        template = 'factoid-%s.irc' % text.tag.lower()
    context = Context(request.__dict__)
    rendered = Template(text.text).render(context)
    d = {'factoid': key, 'verb': text.verb, 'text': rendered}
    if text.tag == 'action':
        method='ACTION'
    else:
        method='PRIVMSG'
    return render_to_response(request.reply_recipient, template, d,
                              method=method)

@require_addressing
@require_chanop
def literal(request, key='', **kwargs):
    factoid = get_object_or_404(Factoid, fact__iexact=normalize_factoid_key(key))
    responses = factoid.factoidresponse_set.filter(disabled__exact=None)
    # XXX: This *really* needs to become a template.
    text = key
    verb = ''
    if factoid.protected:
        text += ' [LOCKED] '
    for response in responses.order_by('verb', 'created'):
        if response.verb != verb:
            verb = response.verb
            text += ' =%s= ' % verb
        else:
            text += '|'
        if response.tag:
            text += '<%s> ' % response.tag
        text += '%s' % response.text

    return IRCResponse(request.reply_recipient, text)

@require_addressing
def edit(request, key='', pattern='', replacement='', re_flags='',
         **kwargs):
    factoid = get_object_or_404(Factoid,
            fact__iexact=normalize_factoid_key(key))
    edited = factoid.edit_responses(pattern, re_flags, replacement,
            request.nick)
    if edited:
        return render_to_reply(request, 'factoid.irc',
                {'factoid': key, 'verb': edited.verb,
                    'text': edited.text})
    return render_error(request,
                        'No response in %s contained your pattern' % key)

# Undos of various stripes 
@require_addressing
@require_chanop
def delete(request, key='', pattern='.', re_flags='', **kwargs):
    factoid = get_object_or_404(Factoid,
            fact__iexact=normalize_factoid_key(key))
    deleted = factoid.delete_response(pattern, re_flags, request.nick)
    if not deleted:
        return render_error(
                request, 'No response in %s contained your pattern' % key)
    return render_quick_reply(request, "ack.irc")

@require_addressing
@require_chanop
def undelete(request, key='', pattern='.', re_flags='', **kwargs):
    factoid = get_object_or_404(Factoid,
            fact__iexact=normalize_factoid_key(key))
    undeleted = factoid.undelete_response(pattern, re_flags, request.nick)
    if not undeleted:
        return render_error(request,
                'No deleted response found for %s' % key)
    return render_quick_reply(request, "ack.irc")

@require_addressing
@require_chanop
def unedit(request, key='', pattern='.', re_flags='', **kwargs):
    factoid = get_object_or_404(Factoid,
            fact__iexact=normalize_factoid_key(key))
    factoid.unedit_response(pattern, re_flags, request.nick)
    return render_quick_reply(request, "ack.irc")
