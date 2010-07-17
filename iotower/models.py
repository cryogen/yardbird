import re
from datetime import datetime

from django.db import models
from django.db.models import Q

try:
    from yardbird.signals import request_started, request_finished
except: # pragma: no cover
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
    def search_responses(self, pattern, re_flags,
            queries=(Q(disabled__exact=None),), multiple=False,
            sort_fields=None):
        pat, count = get_pattern(pattern, re_flags)
        responses = self.factoidresponse_set.filter(*queries)
        if sort_fields:
            responses = responses.order_by(*sort_fields)
        for response in responses:
            if pat.search(response.text):
                yield response
    def edit_responses(self, pattern, flags, replacement, editor):
        pat, count = get_pattern(pattern, flags)
        for response in self.search_responses(pattern, flags):
            newtext = pat.sub(replacement, response.text, count)
            edited = response.replace(newtext, editor)
            return edited
        return False
    def unedit_response(self, pattern, flags, editor):
        for response in self.search_responses(pattern, flags,
                sort_fields=('-created',)):
            oldresponse = self.factoidresponse_set.get(
                    disabled__exact=response.created)
            edited = response.replace(oldresponse.text, editor)
            return edited
    def delete_response(self, pattern, flags, editor):
        deleted_successfully = False
        for response in self.search_responses(pattern, flags,
                sort_fields=('-created',)):
            response.disable(editor)
            deleted_successfully = True
        return deleted_successfully
    def undelete_response(self, pattern, flags, editor):
        deleted = (Q(disabled__isnull=False),)
        for response in self.search_responses(pattern, flags,
                queries=deleted, sort_fields=('-disabled',)):
            return response.undisable()
        return False

    def __unicode__(self):
        """
        >>> Factoid('blorpy')
        <Factoid: blorpy False>
        """
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
    def replace(self, text, creator):
        """Replacement of FactoidResponses works by creating a new
        FactoidResponse and marking self as disabled."""
        edited = FactoidResponse(fact=self.fact, verb=self.verb,
                tag=self.tag, text=text, created_by=creator)
        edited.save() # To generate creation time.
        self.disabled = edited.created
        self.disabled_by = edited.created_by
        self.save()
        return edited
    def disable(self, deleter):
        self.disabled = datetime.now()
        self.disabled_by = deleter
        self.save()
        return True
    def undisable(self):
        self.disabled = None
        self.disabled_by = None
        self.save()
        return True

    def __unicode__(self):
        """
        >>> blorpy = Factoid('blorpy')
        >>> blorpy.save()
        >>> fr = FactoidResponse(fact=blorpy, text='a troll',
        ... created_by='SpaceHobo')
        >>> fr.save()
        >>> fr
        <FactoidResponse: [1] ... <SpaceHobo> blorpy =is= a troll>
        >>> fr.disabled = fr.created; fr.disabled_by = fr.created_by
        >>> fr.save()
        >>> fr
        <FactoidResponse: [1] <SpaceHobo> ...-... <SpaceHobo>: blorpy =is= a troll>
        """
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

def normalize_factoid_key(key):
    key = key.lower()
    key = re.sub(r'(?u)[^\w\s]+', '', key)
    key = re.sub(r'(?u)\s+', ' ', key)
    if 1 <= len(key) <= 64:
        return key
    raise(OverflowError, "Normalized key '%s' not fit for database" % key)

def get_pattern(pattern, re_flags):
    flags = re.UNICODE
    count = 1
    if 'i' in re_flags:
        flags |= re.IGNORECASE
    if 'g' in re_flags:
        count = 0
    pat = re.compile(pattern, flags)
    return pat, count


def generate_statistics():
    fr = FactoidResponse.objects
    oldest_response = fr.all()[0]
    earliest_date = oldest_response.created.replace(microsecond=0)
    num_factoids = Factoid.objects.count()
    num_edits = fr.count()
    num_active_responses = fr.filter(disabled__exact=None).count()
    return ('Since %s I have performed %d edits on %d factoids ' +
            'containing %d active responses',
            (earliest_date, num_edits, num_factoids, num_active_responses))

# Demonstration of a signal handler designed to detect 242 sightings.
auspicious_re = re.compile(r'2\D*4\D*2')

def sighting(sender, **kwargs):
    if 'request' in kwargs:
        req = kwargs['request']
        if auspicious_re.search(req.message):
            sender.notice(req.reply_recipient.encode('utf-8'),
                    '242 sighting!')

request_started.connect(sighting)
