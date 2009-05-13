from django.db import models

class BandName(models.Model):
    """Duuude, that would be so totally sweet as a band name, duuude"""
    band = models.CharField(maxlength=50)
    def __unicode__(self):
        return u'%s' % (self.band)

class Lines(models.Model):
    """Hookers and Blow"""
    msg = models.TextField()

    def __unicode__(self):
        return u'%s' % self.msg

MOOD_CHOICES = ( ":<", ":(", ":|", ":)", ":D" )

class BucketFacts(models.Model):
    """Bucket is made of Facts, not Fictions."""
    fact = models.CharField(maxlength=64)
    tidbit = models.TextField()
    verb = models.CharField(maxlength=16, default=u'is')
    re = models.BooleanField()
    protected = models.BooleanField()
    mood = models.CharField(maxlength=2, choices=MOOD_CHOICES,
                            blank=True, null=True)
    chance = models.PositiveSmallIntegerField(blank=True, null=True)
    
    def __unicode__(self):
        return u'%s %s %s %s' % (self.fact, self.verb, self.tidbit,
                                 self.mood)

    class Meta:
        unique_together = ("fact", "tidbit", "verb")
