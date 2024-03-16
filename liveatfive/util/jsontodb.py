import os
import django
import sys
import json
import luscioustwitch
import datetime

sys.path.append("../../")
  
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from liveatfive.models import TwitchVideo

with open("./videos.json", 'r') as videodata:
  videojson = json.load(videodata)
  
  for id in videojson["list"]:
    video = videojson["list"][id]
    
    videomodel = TwitchVideo(
      vod_id = video["id"],
      stream_id = video["stream_id"],
      user_id = video["user_id"],
      user_login = video["user_login"],
      user_name = video["user_name"],
      title = video["title"],
      description = video["description"],
      created_at = datetime.datetime.strptime(video["created_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
      published_at = datetime.datetime.strptime(video["published_at"], luscioustwitch.TWITCH_API_TIME_FORMAT).replace(tzinfo = datetime.timezone.utc),
      url = video["url"],
      thumbnail_url = video["thumbnail_url"],
      viewable = video["viewable"],
      view_count = video["view_count"],
      language = video["language"],
      vod_type = video["type"],
      duration = video["duration"],
    )
    
    videomodel.save()