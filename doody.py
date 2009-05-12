from yardbird import IRCResponse

def foo(request):
    if request.channel:
        recipient = request.channel
    else:
        recipient = request.user
    nick = request.user.split('!', 1)[0]
    return IRCResponse(recipient, u'foo on %s!' % nick)

def bar(request):
    if request.channel:
        recipient = request.channel
    else:
        recipient = request.user
    nick = request.user.split('!', 1)[0]
    return IRCResponse(recipient, u'BAR UPON %s!' % nick.upper())

