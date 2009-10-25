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

def normalize_factoid_key(key):
    key = key.lower()
    key = re.sub(r'(?u)[^\w\s]+', '', key)
    key = re.sub(r'(?u)\s+', ' ', key)
    if 1 <= len(key) <= 64:
        return key
    raise(exceptions.ValidationError,
                "Normalized key '%s' not fit for database" % key)

def generate_statistics():
    fr = FactoidResponse.objects
    oldest_response = fr.get(pk=1)
    earliest_date = oldest_response.created.replace(microsecond=0)
    num_factoids = Factoid.objects.count()
    num_edits = fr.count()
    num_active_responses = fr.filter(disabled__exact=None).count()
    return ('Since %s I have performed %d edits on %d factoids ' +
            'containing %d active responses',
            (earliest_date, num_edits, num_factoids, num_active_responses))

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
        factext = FactoidResponse(fact=factoid, verb=verb, text=value,
                                  tag=tag, created_by=request.nick)
        factext.save()
        if request.addressed:
            return render_quick_reply(request, "ack.irc")
    # If we got this far, it's worth trying to see if this is just a
    # factoid with 'is' or 'are' in the key.
    try:
        return trigger(request, key=request.message)
    except Http404, exceptions.ValidationError:
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
        template = 'factoid-%s.irc' % text.tag
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

def get_factoid_and_pattern(key, pattern, re_flags):
    flags = re.UNICODE
    count = 1
    if 'i' in re_flags:
        flags |= re.IGNORECASE
    if 'g' in re_flags:
        count = 0
    pat = re.compile(pattern, flags)
    factoid = get_object_or_404(Factoid, fact__iexact=normalize_factoid_key(key))
    return factoid, pat, count

def regex_operation_on_factoid(key, pattern, re_flags, queries, fn,
        multiple=False, sort_fields=None):
    factoid, pat, count = get_factoid_and_pattern(key, pattern, re_flags)
    responses = factoid.factoidresponse_set.filter(*queries)
    if sort_fields:
        responses = responses.order_by(*sort_fields)
    ret = []
    for response in responses:
        if pat.search(response.text):
            answer = fn(response, pattern=pat, factoid=factoid,
                    responses=responses)
            if answer and multiple and count:
                ret.append(answer)
            elif answer:
                return answer
    return ret

def replace_response(old_response, new_text, created_by):
    edited = FactoidResponse(fact=old_response.fact,
            verb=old_response.verb, tag=old_response.tag, text=new_text,
            created_by=created_by)
    edited.save() # To generate creation time.
    old_response.disabled = edited.created
    old_response.disabled_by = edited.created_by
    old_response.save()
    return edited

@require_addressing
def edit(request, key='', pattern='', replacement='', re_flags='',
         **kwargs):
    factoid, pat, count = get_factoid_and_pattern(key, pattern, re_flags)
    responses = factoid.factoidresponse_set.filter(disabled__exact=None)
    for response in responses:
        if pat.search(response.text):
            newtext = pat.sub(replacement, response.text, count)
            edited = replace_response(response, newtext, request.nick)
            return render_to_reply(request, 'factoid.irc',
                                   {'factoid': key, 'verb': edited.verb,
                                    'text': edited.text})
    return render_error(request,
                        'No response in %s contained your pattern' % key)

# Undos of various stripes 
@require_addressing
@require_chanop
def delete(request, key='', pattern='.', re_flags='', **kwargs):
    def delete_response(response, **kwargs):
        response.disabled = datetime.now()
        response.disabled_by = request.nick
        response.save()
        return response.text

    not_deleted = (Q(disabled__exact=None),)
    deleted = regex_operation_on_factoid(key, pattern, re_flags,
            not_deleted, delete_response, multiple=True,
            sort_fields=('-created',))
    if not deleted:
        return render_error(
                request, 'No response in %s contained your pattern' % key)
    return render_quick_reply(request, "ack.irc")

@require_addressing
@require_chanop
def undelete(request, key='', pattern='.', re_flags='', **kwargs):
    def undelete_response(response, **kwargs):
        response.disabled = None
        response.disabled_by = None
        response.save()
        return response.text

    deleted = (Q(disabled__isnull=False),)
    undeleted = regex_operation_on_factoid(key, pattern, re_flags,
            deleted, undelete_response, sort_fields=('-disabled',))
    if not undeleted:
        return render_error(request,
                'No deleted response found for %s' % key)
    return render_quick_reply(request, "ack.irc")

@require_addressing
@require_chanop
def unedit(request, key='', pattern='.', re_flags='', **kwargs):
    def unedit_response(response, factoid=None, **kwargs):
        try:
            oldresponse = factoid.factoidresponse_set.get(
                    disabled__exact=response.created)
        except:
            return None
        edited = replace_response(response, oldresponse.text,
                request.nick)
        return edited.text

    edited = (Q(disabled__exact=None),)
    unedited = regex_operation_on_factoid(key, pattern, re_flags,
            edited, unedit_response, sort_fields=('-created',))
    if not unedited:
        return render_error(request,
                'No edited response in %s contained your pattern' % key)
    return render_quick_reply(request, "ack.irc")
