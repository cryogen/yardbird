from django.db import models

MOOD_CHOICES = ( (":<", ":<"),
                 (":(", ":("),
                 (":|", ":|"),
                 (":)", ":)"),
                 (":D", ":D") )

class Factoid(models.Model):
    """Bucket is made of Facts, not Fictions."""
    fact = models.CharField(max_length=64, primary_key=True)
    protected = models.BooleanField(default=False)
    def __unicode__(self):
        return u'%s %s' % (self.fact, self.protected)

class FactoidResponse(models.Model):
    """Factoid Responses are text pointing to a factoid entry"""
    fact = models.ForeignKey(Factoid)
    verb = models.CharField(max_length=16, default=u'is')
    text = models.TextField()
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

def my_handler(sender, **kwargs):
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    print("SIGNALLLLL")
    pp.pprint(sender)
    pp.pprint(kwargs)

from django.core.signals import request_started, request_finished, got_request_exception

request_started.connect(my_handler)
request_finished.connect(my_handler)
got_request_exception.connect(my_handler)
