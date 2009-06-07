#!/usr/bin/python

from django.contrib import admin
from iotower import models

admin.site.register(models.Factoid)
admin.site.register(models.FactoidResponse)

