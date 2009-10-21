import re

from django.db import models

try:
    from yardbird.signals import request_started, request_finished
except:
    print """ ***** NOTA BENE *****
The IOTower app is written for Yardbird, which is a chat bot system
for Django.  It is not generally useful from the Web, and as such you
almost certainly want to install Yardbird into your PYTHONPATH before
proceeding.  

To acquire Yardbird, visit:
    http://zork.net/~nick/yardbird/
or for source tarballs and packages, go to:
    http://zork.net/pub/yardbird/"""
    raise

# Never quite figured out what bucket did with these, but they're fun!
# This may be the sort of thing we keep in a factoid or otherwise in the
# DB.
MOOD_CHOICES = ( (":<", ":<"),
                 (":(", ":("),
                 (":|", ":|"),
                 (":)", ":)"),
                 (":D", ":D") )

class Factoid(models.Model):
    """Dumont is made of Facts, not Fictions."""
    fact = models.CharField(max_length=64, primary_key=True)
    protected = models.BooleanField(default=False)
    def __unicode__(self):
        return u'%s %s' % (self.fact, self.protected)

class FactoidResponse(models.Model):
    """Factoid Responses are text pointing to a factoid entry"""
    fact = models.ForeignKey(Factoid)
    verb = models.CharField(max_length=16, default=u'is')
    text = models.TextField()
    tag = models.SlugField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=30)
    disabled = models.DateTimeField(blank=True, null=True)
    disabled_by = models.CharField(max_length=30,blank=True, null=True)
    def __unicode__(self):
        if self.disabled:
            return u'[%s] <%s> %s-%s <%s>: %s =%s= %s' % (self.pk,
                                                          self.created_by,
                                                          self.created,
                                                          self.disabled,
                                                          self.disabled_by,
                                                          self.fact.fact,
                                                          self.verb,
                                                          self.text)
        return u'[%s] %s <%s> %s =%s= %s' % (self.pk, self.created,
                                             self.created_by,
                                             self.fact.fact, self.verb,
                                             self.text)
    class Meta:
        unique_together = ("fact", "verb", "text", "created")

# Demonstration of a signal handler designed to detect 242 sightings.
auspicious_re = re.compile(r'2\D*4\D*2')

def sighting(sender, **kwargs):
    if 'request' in kwargs:
        req = kwargs['request']
        if auspicious_re.search(req.message):
            sender.notice(req.reply_recipient.encode('utf-8'),
                    '242 sighting!')

request_started.connect(sighting)
