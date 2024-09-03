from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.http import int_to_base36
import datetime
from luscioustwitch import TWITCH_API_TIME_FORMAT
from django.db.models.signals import pre_save

from .config import *
from .util.timeutil import *

# Create your models here.

class CreatorInfo(models.Model):
  creator_id = models.IntegerField(primary_key = True, editable = False)
  
  is_live = models.BooleanField(default = False)
  was_live = models.BooleanField(default = False)
  average_offset = models.FloatField(default = 0.0)
  longest_early_streak = models.IntegerField(default = 0)
  longest_ontime_streak = models.IntegerField(default = 0)
  longest_late_streak = models.IntegerField(default = 0)

class TwitchVideo(models.Model):
  vod_id = models.CharField(max_length = 128, default = "", unique = True)
  stream_id = models.CharField(max_length = 128, default = "", blank = True)
  user_id = models.CharField(max_length = 128, default = "", blank = True)
  user_login = models.CharField(max_length = 128, default = "", blank = True)
  user_name = models.CharField(max_length = 128, default = "", blank = True)
  title = models.TextField(default = "", blank = True)
  description = models.TextField(default = "", blank = True)
  created_at = models.DateTimeField("created at", default = datetime.datetime.now, blank = True)
  published_at = models.DateTimeField("published at", default = datetime.datetime.now, blank = True)
  url = models.TextField(default = "", blank = True)
  thumbnail_url = models.TextField(default = "", blank = True)
  viewable = models.CharField(max_length = 64, default = "", blank = True)
  view_count = models.IntegerField(default = 0, blank = True)
  language = models.CharField(max_length = 32, default = "", blank = True)
  vod_type = models.CharField(max_length = 64, default = "", blank = True)
  duration = models.CharField(max_length = 64, default = "", blank = True)
  
class Punctuality(models.IntegerChoices):
  EARLY  = (0, _("Early"))
  ONTIME = (1, _("On time"))
  LATE   = (2, _("Late"))
  
class Weekday(models.IntegerChoices):
  MON = (0, _("Monday"))
  TUE = (1, _("Tuesday"))
  WED = (2, _("Wednesday"))
  THU = (3, _("Thursday"))
  FRI = (4, _("Friday"))
  SAT = (5, _("Saturday")) 
  SUN = (6, _("Sunday"))
  
class StreamInfoManager(models.Manager):
  def create_streaminfo(self, date, start_time):
    streaminfo = self.create(date = date, start_time = start_time)
      
    streaminfo.calculate_punctuality()
    streaminfo.calculate_offset()
    streaminfo.calculate_weekday()
    
    return streaminfo
  
STREAMINFO_DATE_FORMAT = "%Y%m%d"
class StreamInfo(models.Model):
  date = models.CharField(max_length = 8, primary_key = True, editable = False)
  
  start_time = models.DateTimeField("start time", default = datetime.datetime.now)
  
  offset = models.FloatField(default = 0.0)
  punctuality = models.IntegerField(choices = Punctuality.choices, default = Punctuality.LATE)
  weekday = models.IntegerField(choices = Weekday.choices, default = Weekday.SUN)
  
  objects = StreamInfoManager()
  
  def to_dict(self, twentyfour = False):
    return {
      "offset": self.offset,
      "punctuality": self.punctuality,
      "weekday": self.weekday,
      "time": self.get_pretty_start_time(twentyfour),
      "date": self.get_pretty_date(), 
    }
    
  def calculate_punctuality(self, autosave = False):
    local_start_time = utc_to_local(self.start_time, local_tz = TIMEZONE).time()

    if local_start_time < ONTIME_START:
      self.punctuality = Punctuality.EARLY
    elif local_start_time >= ONTIME_START and local_start_time < ONTIME_END:
      self.punctuality = Punctuality.ONTIME
    else:
      self.punctuality = Punctuality.LATE
    
    if autosave:
      self.save()
  
  def calculate_offset(self, autosave = False):
    local_start_time = utc_to_local(self.start_time, local_tz = TIMEZONE).time()
    
    td = timediff(local_start_time, GOAL_TIME)
    self.offset = td.seconds + (24.0 * 60.0 * 60.0 * td.days)
    
    if autosave:
      self.save()
    
  def calculate_weekday(self, autosave = False):
    local_start_time = utc_to_local(self.start_time, local_tz = TIMEZONE)
    self.weekday = local_start_time.weekday()
    
    if autosave:
      self.save()
    
  def get_pretty_date(self):
    local_start_time = utc_to_local(self.start_time, local_tz = TIMEZONE)
    
    return local_start_time.strftime("%Y-%m-%d")
      
  def get_pretty_start_time(self, twentyfour = False):
    local_start_time = utc_to_local(self.start_time, local_tz = TIMEZONE)
    
    if twentyfour:
      return local_start_time.strftime("%H:%M:%S")
    else:
      return local_start_time.strftime("%I:%M:%S %p")
  
  def set_start_time(self, st : datetime.datetime, initialize = False):
    if initialize or (st < self.start_time):
      self.start_time = st
      
      self.calculate_punctuality()
      self.calculate_offset()
      self.calculate_weekday()
      
      self.save()