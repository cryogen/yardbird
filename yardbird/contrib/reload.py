from yardbird.shortcuts import render_to_response
from yardbird.utils.decorators import require_addressing, require_chanop

@require_addressing
@require_chanop
def reload(request, *args, **kwargs):
    return render_to_response(request.reply_recipient, "reload.irc", {},
            method='RESET')

