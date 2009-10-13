from django.conf import settings
from django.core.exceptions import PermissionDenied
from yardbird.shortcuts import render_error, render_silence

def require_addressing(function):
    """Decorates a function to return an error if the request neither is
    a private /msg nor contains the bot's nick as the first word."""
    def new(request, *args, **kwargs):
        if request.addressed:
            return function(request, *args, **kwargs)
        if 'addressee' in kwargs:
            return render_silence()
        else:
            return render_error(request,
                'You must address me to perform this operation.')
    return new

def require_chanop(function):
    """Decorates a function to return an error if the requestor lacks
    operator status in the channel blessed in the settings."""
    def new(request, *args, **kwargs):
        for chan in request.privileged_channels:
            chan = chan.lower()
            if request.mask in request.chanmodes[chan]:
                if '@' in request.chanmodes[chan][request.mask]:
                    return function(request, *args, **kwargs)
        raise PermissionDenied
    return new
