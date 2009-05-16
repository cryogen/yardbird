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
    def __unicode__(self):
        return u'%s <%s> %s' % (self.fact.fact, self.verb, self.text)
    class Meta:
        unique_together = ("fact", "verb", "text")
