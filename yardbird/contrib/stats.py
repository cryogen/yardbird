from django.conf import settings
from yardbird.shortcuts import render_to_reply
from yardbird.utils.decorators import require_addressing

@require_addressing
def gather_statistics(request, addressee='', template_name='stats.irc',
        dictionary={}, context_instance=None):
    dictionary['statistics'] = []
    for app in settings.INSTALLED_APPS:
        try:
            m = __import__(app + '.ircviews')
            if hasattr(m.ircviews, 'generate_statistics'):
                format_string, values = m.ircviews.generate_statistics()
                dictionary['statistics'].append(format_string % values)
        except ImportError:
            pass
    return render_to_reply(request, template_name, dictionary,
        context_instance)


