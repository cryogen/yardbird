#!/usr/bin/python

from django.template.loader import render_to_string
from irc import IRCResponse

def render_to_response(recipient, template_name, dictionary={},
                       context_instance=None, method='PRIVMSG'):
    text = render_to_string(template_name, dictionary, context_instance)
    dictionary['method'] = method
    return IRCResponse(recipient, text, **dictionary)

def render_to_reply(request, template_name, dictionary={},
                    context_instance=None):
    """render_to_reply crafts a response based on attributes of the
    request.  It also tries to fill in the "addressee" for reply
    addressing logic if the incoming dictionary does not already specify
    one."""
    if 'addressee' not in  dictionary:
        dictionary['addressee'] = request.addressee
    return render_to_response(request.reply_recipient, template_name,
                              dictionary, context_instance,
                              request.method)

def render_quick_reply(request, template_name):
    """render_quick_reply just renders the template with the request as
    the context dictionary."""
    return render_to_reply(request, template_name, request.__dict__)

def render_silence(*args, **kwargs):
    return IRCResponse('', '', 'QUIET')

def render_error(request, msg):
    return IRCResponse(request.nick, msg, method='NOTICE')

# This doesn't seem to belong here, and may only be useful as a function
# in the errorback's scope. Note also how it duplicates some of
# render_error.  
def reply(bot, request, message, *args, **kwargs):
    recipient = request.user.split('!', 1)[0]
    res = IRCResponse(recipient, message % kwargs, method='NOTICE')
    return bot.methods[res.method](res.recipient, res.data.encode('utf-8'))
