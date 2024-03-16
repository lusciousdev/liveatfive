
from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import generic
from django.conf import settings

import typing

from .models import *
from .tasks import *
from .config import *
from .util.timeutil import *

# Create your views here.
class IndexView(generic.ListView):
  model = StreamInfo
  template_name = "liveatfive/index.html"
  
  def get_queryset(self):
    todaydt = utc_to_local(dt.datetime.now(tz = dt.timezone.utc), TIMEZONE)
    year = todaydt.strftime("%Y")
    
    return StreamInfo.objects.filter(date__startswith = year)
  
class StatsView(generic.TemplateView):
  template_name = "liveatfive/stats.html"
  
class FAQView(generic.TemplateView):
  template_name = "liveatfive/faq.html"