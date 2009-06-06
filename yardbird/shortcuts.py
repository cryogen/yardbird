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
    return render_to_response(request.reply_recipient, template_name,
                              dictionary, context_instance,
                              request.method)

def render_silence(*args, **kwargs):
    return IRCResponse('', '', 'QUIET')

def render_quick_reply(request, template_name, dictionary={}):
    dictionary.update(request.__dict__)
    return render_to_response(request.reply_recipient, template_name,
                              dictionary)

def render_error(request, msg):
    return IRCResponse(request.nick, msg, method='NOTICE')

def reply(bot, request, message, *args, **kwargs):
    recipient = request.user.split('!', 1)[0]
    res = IRCResponse(recipient, message % kwargs, method='NOTICE')
    return bot.methods[res.method](res.recipient, res.data.encode('utf-8'))
