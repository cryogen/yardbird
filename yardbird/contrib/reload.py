from yardbird.irc import IRCResponse
from yardbird.utils.decorators import require_addressing, require_chanop

@require_addressing
@require_chanop
def reload(request, *args, **kwargs):
    return IRCResponse(request.reply_recipient, 'Reload successful.',
            method='RESET')

