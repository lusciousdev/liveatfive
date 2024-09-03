from django.conf import settings
from celery import Celery, shared_task
from celery.schedules import crontab
import luscioustwitch

from .models import *
from .config import *
from .util.timeutil import *

@shared_task
def calculate_offset_and_streaks():
  print("Calculating average offset and longest streaks.")
  
  total_offset = 0
  total_streams = 0
  
  streak_type = None
  streak_length = 0
  
  longest_early_streak = 0
  longest_ontime_streak = 0
  longest_late_streak = 0
  
  for streaminfo in StreamInfo.objects.all().order_by("date"):
    total_streams += 1
    total_offset += streaminfo.offset
    
    if streak_type is None:
      streak_type = streaminfo.punctuality
      streak_length = 1
    elif (streaminfo.punctuality == streak_type):
      streak_length += 1
    else:
      if streak_type == Punctuality.EARLY:
        longest_early_streak = streak_length if (streak_length > longest_early_streak) else longest_early_streak
      elif streak_type == Punctuality.ONTIME:
        longest_ontime_streak = streak_length if (streak_length > longest_ontime_streak) else longest_ontime_streak
      elif streak_type == Punctuality.LATE:
        longest_late_streak = streak_length if (streak_length > longest_late_streak) else longest_late_streak
      
      streak_type = streaminfo.punctuality
      streak_length = 1
    
  try:
    creator_info = CreatorInfo.objects.get(creator_id = CREATOR_ID)
    creator_info.average_offset = (total_offset / total_streams)
    creator_info.longest_early_streak = longest_early_streak
    creator_info.longest_ontime_streak = longest_ontime_streak
    creator_info.longest_late_streak = longest_late_streak
    creator_info.save()
  except CreatorInfo.DoesNotExist:
    creator_info = CreatorInfo(creator_id = CREATOR_ID, 
                               is_live = False, 
                               was_live = False, 
                               average_offset = (total_offset / total_streams),
                               longest_early_streak = longest_early_streak,
                               longest_ontime_streak = longest_ontime_streak,
                               longest_late_streak = longest_late_streak)
    creator_info.save()

@shared_task()
def get_creator_info():
  print(f"Fetching info for {CREATOR}")

  twitch_api = luscioustwitch.TwitchAPI({ "CLIENT_ID" : settings.TWITCH_API_CLIENT_ID, "CLIENT_SECRET": settings.TWITCH_API_CLIENT_SECRET })
  
  video_params = {
    "user_id": CREATOR_ID,
    "period": "all",
    "sort": "time",
    "type": "archive"
  }
  
  vods = twitch_api.get_all_videos(video_params)
  
  print(f"Got {len(vods)} videos from the Twitch API")
  for vod in vods:
    try:
      existing_video_object : TwitchVideo
      existing_video_object, created = TwitchVideo.objects.get_or_create(vod_id = vod["id"])
      
      existing_video_object.stream_id     = vod["stream_id"]
      existing_video_object.user_id       = vod["user_id"]
      existing_video_object.user_login    = vod["user_login"]
      existing_video_object.user_name     = vod["user_name"]
      existing_video_object.title         = vod["title"]
      existing_video_object.description   = vod["description"]
      existing_video_object.created_at    = datetime.datetime.strptime(vod["created_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc)
      existing_video_object.published_at  = datetime.datetime.strptime(vod["published_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc)
      existing_video_object.url           = vod["url"]
      existing_video_object.thumbnail_url = vod["thumbnail_url"]
      existing_video_object.viewable      = vod["viewable"]
      existing_video_object.view_count    = vod["view_count"]
      existing_video_object.language      = vod["language"]
      existing_video_object.vod_type      = vod["type"]
      existing_video_object.duration      = vod["duration"]
  
      existing_video_object.save()
    except Exception as e:
      print(f"unable to parse twitch vod response: {e}")
  
  for vod in TwitchVideo.objects.all():
    voddate = utc_to_local(vod.created_at, TIMEZONE).strftime(STREAMINFO_DATE_FORMAT)

    try:
      streaminf = StreamInfo.objects.get(date = voddate)
      
      streaminf.set_start_time(vod.created_at)
      streaminf.save()
    except StreamInfo.DoesNotExist:
      newstreaminfo = StreamInfo.objects.create_streaminfo(date = voddate, start_time = vod.created_at)
      newstreaminfo.save()
      
  is_live = twitch_api.is_user_live(CREATOR_ID)
  
  today = utc_to_local(dt.datetime.now(tz = dt.timezone.utc), TIMEZONE).strftime(STREAMINFO_DATE_FORMAT)
  
  was_live = False
  try:
    todays_stream_info = StreamInfo.objects.get(date = today)
    was_live = True
  except StreamInfo.DoesNotExist:
    was_live = False
    
  try:
    creator_info = CreatorInfo.objects.get(creator_id = CREATOR_ID)
    
    creator_info.is_live = is_live
    creator_info.was_live = was_live
    creator_info.save()
  except CreatorInfo.DoesNotExist:
    creator_info = CreatorInfo(creator_id = CREATOR_ID, is_live = is_live, was_live = was_live, average_offset = 0.0)
    creator_info.save()