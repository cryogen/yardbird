from yardbird import IRCResponse

def foo(request):
    nick = request.user.split('!', 1)[0]
    if request.channel != request.nick:
        recipient = request.channel
    else:
        recipient = nick
    return IRCResponse(recipient, u'foo on %s!' % nick)

def bar(request):
    nick = request.user.split('!', 1)[0]
    if request.channel != request.nick:
        recipient = request.channel
    else:
        recipient = nick
    return IRCResponse(recipient, u'BAR UPON %s!' % nick.upper())

