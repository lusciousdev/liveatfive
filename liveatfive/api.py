from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, Http404, HttpResponseRedirect, JsonResponse
from celery import Celery, shared_task
from celery.schedules import crontab
import luscioustwitch
import calendar
import re

from .models import *
from .config import *
from .util.timeutil import *

DATE_REGEX = re.compile(r"([0-9]{4})[\-\/ ]?([0-9]{1,2})?")

def get_when_live_string(user_id = "", provider = None):
  if (user_id != "") and (str(user_id) == str(CREATOR_ID)):
    return f"Shouldn't you know, @{CREATOR}."
  
  now = utc_to_local(dt.datetime.now(tz=dt.timezone.utc), TIMEZONE)
  whenLive = ""
  
  isDiscord = provider == 'discord'
  
  bhisdhm = "<:BoyHowdyISureDoHateMondays:664006532865851404>" if isDiscord else "BoyHowdyISureDoHateMondays"
  madgelate = '<a:MadgeLate:1082875805392195584>' if isDiscord else 'MadgeLate'
  dinkdonk = '<a:DinkDonk:1095478933350260836>' if isDiscord else 'DinkDonk'
  pause = '<:PauseChamp:796928958527963177>' if isDiscord else 'PauseChamp'
  stsmg = '<:PauseChamp:796928958527963177>' if isDiscord else 'StartTheStreamMyGuy'
  
  try:
    creator_info = CreatorInfo.objects.get(creator_id = CREATOR_ID)
  except CreatorInfo.DoesNotExist:
    return ""
  
  if creator_info.is_live:
    whenLive = f"itswill is live now {dinkdonk} ."
  elif creator_info.was_live:
    whenLive = "Today's stream has ended."
  elif now.weekday() == 3: # Thursday
    whenLive = f"Probably no stream today BoyHowdyISureDoHateThursdays."
  elif now.time() < GOAL_TIME:
    timeStr = smartfmtdelta(timediff(GOAL_TIME, now.time()))
    whenLive = f"itswill should be live in {timeStr} {pause} ."
  elif now.time() <= ONTIME_END:
    timeStr = smartfmtdelta(timediff(ONTIME_END, now.time()))
    whenLive = f"Respect the 15 minute buffer. He still has {timeStr} left {stsmg} ."
  else:
    timeStr = smartfmtdelta(timediff(now.time(), ONTIME_END))
    whenLive = f"itswill should've been live {timeStr} ago {madgelate} ."
  
  return whenLive

@csrf_exempt
def get_today(request):
  if request.method != "GET":
    return JsonResponse({ "error": "Invalid request type." }, 501)
  
  todaydt = utc_to_local(dt.datetime.now(tz = dt.timezone.utc), TIMEZONE)
  sixhrsago_dt = utc_to_local(dt.datetime.now(tz = dt.timezone.utc) - dt.timedelta(hours = 6), TIMEZONE)
  
  try:
    creator_info = CreatorInfo.objects.get(creator_id = CREATOR_ID)
  except CreatorInfo.DoesNotExist:
    return ""
  
  if not (creator_info.is_live or creator_info.was_live):
    return HttpResponse(f"itswill has not gone live yet today.", 200)
  
  try:
    streaminfo = StreamInfo.objects.get(date = todaydt.strftime(STREAMINFO_DATE_FORMAT))
  except StreamInfo.DoesNotExist:
    try:
      streaminfo = StreamInfo.objects.get(date = sixhrsago_dt.strftime(STREAMINFO_DATE_FORMAT))
    except StreamInfo.DoesNotExist:
      return HttpResponse("No stream data for today.", 200)
  
  return HttpResponse(f"Will was {streaminfo.get_punctuality_display().lower()} today. He went live at {streaminfo.get_pretty_start_time()}.", 200)

@csrf_exempt
def get_record(request):
  if request.method != "GET":
    return JsonResponse({ "error": "Invalid request type." }, 501)
  
  todaydt = utc_to_local(dt.datetime.now(tz = dt.timezone.utc), TIMEZONE)
  
  plaintext = ("plaintext" in request.GET)
  
  weekday_arg : str = request.GET.get("weekday", None)
  user_id_arg : str = request.GET.get("userid", None)
  period_arg : str = request.GET.get("period", None)
  percent_arg : str = request.GET.get("percent", None)
  
  weekday_filter = None
  if weekday_arg is not None:
    weekdaystr = weekday_arg.lower()
    if weekdaystr in ['m', 'mon', 'monday', '0']:
      weekday_filter = Weekday.MON
    elif weekdaystr in ['t', 'tues', 'tuesday', '1']:
      weekday_filter = Weekday.TUE
    elif weekdaystr in ['w', 'wed', 'wednesday', '2']:
      weekday_filter = Weekday.WED
    elif weekdaystr in ['th', 'thurs', 'thursday', '3']:
      weekday_filter = Weekday.THU
    elif weekdaystr in ['f', 'fri', 'friday', '4']:
      weekday_filter = Weekday.FRI
    elif weekdaystr in ['s', 'sat', 'saturday', '5']:
      weekday_filter = Weekday.SAT
    elif weekdaystr in ['su', 'sun', 'sunday', '6']:
      weekday_filter = Weekday.SUN
  
  period_filter = None
  if period_arg is not None:
    date_match = DATE_REGEX.search(period_arg)
    if date_match:
      year = date_match.groups()[0]
      month = None if len(date_match.groups()) < 2 else date_match.groups()[1]
      period_filter = f"{year}" if month == None else f"{year}{month.rjust(2, '0')}"
    elif any(text in period_arg.lower() for text in ["lastyear", "last year"]):
      period_filter = (todaydt - datetime.timedelta(days = 365)).strftime("%Y")
    elif any(text in period_arg.lower() for text in ["currentyear", "current year"]):
      period_filter = todaydt.strftime("%Y")
    elif any(text in period_arg.lower() for text in ["lastmonth", "last month"]):
      period_filter = (todaydt.replace(day=1) - datetime.timedelta(days = 1)).strftime("%Y%m")
    elif any(text in period_arg.lower() for text in ["currentmonth", "current month"]):
      period_filter = todaydt.strftime("%Y%m")
    elif any(text in period_arg.lower() for text in ["alltime", "all", "all time"]):
      period_filter = None
    else:
      period_filter = todaydt.strftime("%Y")
  
  early = 0  
  ontime = 0
  late = 0
  total_streams = 0
  streak_broken = False
  streak_type = None
  streak_type_str = ""
  streak_length = 0
  
  streaminfo_list = StreamInfo.objects.all()
  
  if period_filter is not None:
    streaminfo_list = streaminfo_list.filter(date__startswith = period_filter)
    
  if weekday_filter is not None:
    streaminfo_list = streaminfo_list.filter(weekday = weekday_filter)
    
  streaminfo_list = streaminfo_list.order_by('-date')
    
  for stream in streaminfo_list.all():
    # Count out our current streak
    if streak_type is None:
      streak_type = stream.punctuality
      streak_type_str = stream.get_punctuality_display()
      streak_length = 1
    elif (not streak_broken) and (stream.punctuality == streak_type):
      streak_length += 1
    elif (not streak_broken) and (stream.punctuality != streak_type):
      streak_broken = True
      
    # Count each stream type
    total_streams += 1
    if stream.punctuality == Punctuality.EARLY:
      early += 1
    elif stream.punctuality == Punctuality.ONTIME:
      ontime += 1
    elif stream.punctuality == Punctuality.LATE:
      late += 1
      
  if plaintext:
    perioddt_start = todaydt
    if period_filter is None:
      perioddt_start = datetime.datetime(year = 1971, month = 1, day = 1, hour = 0, minute = 0, second = 0, microsecond = 1, tzinfo = TIMEZONE)
    elif len(period_filter) == 4:
      perioddt_start = datetime.datetime.strptime(period_filter, "%Y").replace(month = 1, day = 1, hour = 0, minute = 0, second = 0, microsecond = 1, tzinfo = TIMEZONE)
    elif len(period_filter) == 6:
      perioddt_start = datetime.datetime.strptime(period_filter, "%Y%m")
      perioddt_start = perioddt_start.replace(day = 1, hour = 0, minute = 0, second = 0, microsecond= 1, tzinfo = TIMEZONE)
      
    perioddt_end = todaydt
    if period_filter is None:
      perioddt_end = todaydt.replace(month = 12, day = 31, hour = 23, minute = 59, second = 59, microsecond= 999999, tzinfo = TIMEZONE)
    elif len(period_filter) == 4:
      perioddt_end = datetime.datetime.strptime(period_filter, "%Y").replace(month = 12, day = 31, hour = 23, minute = 59, second = 59, microsecond= 999999, tzinfo = TIMEZONE)
    elif len(period_filter) == 6:
      perioddt_end = datetime.datetime.strptime(period_filter, "%Y%m")
      perioddt_end = perioddt_end.replace(day = calendar.monthrange(year = perioddt_end.year, month = perioddt_end.month)[1], hour = 23, minute = 59, second = 59, microsecond= 999999, tzinfo = TIMEZONE)
    
    this_year = todaydt.strftime("%Y")
    this_month = todaydt.strftime("%Y%m")
    
    is_creator = (str(user_id_arg) == str(CREATOR_ID))
    pronoun = "He" if not is_creator else "You"
    
    if perioddt_end < todaydt:
      verb = "was" if not is_creator else "were"
    else:
      verb = "has been" if not is_creator else "have been"
    
    range_str = ""
    if period_filter is not None and len(period_filter) == 4:
      range_str = " this year" if period_filter == this_year else f" in {period_filter}"
    elif period_filter is not None and len(period_filter) == 6:
      range_str = " this month" if period_filter == this_month else f" in {perioddt_start.strftime('%B %Y')}"
    
    late = total_streams - ontime - early
    times_ontime_str = ontime if ontime != 100 else "💯"
    times_early_str = early if early != 100 else "💯"
    times_late_str = late if late != 100 else "💯"
    
    percent = False
    if percent_arg is not None:
      percent = any(text in percent_arg.lower() for text in ["%", "percent"])
    
    return_str = f"{get_when_live_string(user_id_arg)} " if perioddt_start <= todaydt <= perioddt_end else ""
    if percent:
      return_str += f"{pronoun} {verb} early {round((early * 100.0) / max(total_streams, 1), 1)}%, on time {round((ontime * 100.0) / max(total_streams, 1), 1)}%, and late {round(((total_streams-ontime-early) * 100.0) / max(total_streams, 1), 1)}% of all streams{range_str}."
    else:
      return_str += f"{pronoun} {verb} early {times_early_str} times, on time {times_ontime_str} times, and late {times_late_str} times{range_str}."
    if perioddt_start <= todaydt <= perioddt_end and streak_length > 1:
      return_str += f" {pronoun} {verb} been {streak_type_str.lower()} {streak_length} streams in a row."
      
    return HttpResponse(return_str, status = 200)
  else:
    resp = {
      'on-time': ontime,
      'early': early,
      'total': total_streams,
      'streak': streak_length,
      'streak-status': streak_type
    }
    return JsonResponse(resp, status = 200)
  

@csrf_exempt
def get_is_live(request):
  if request.method != "GET":
    return JsonResponse({ "error": "Invalid request type." }, 501)
  
  try:
    creator_info = CreatorInfo.objects.get(creator_id = CREATOR_ID)
    resp = { 'live' : 1 if creator_info.is_live else 0, 'waslive' : 1 if creator_info.was_live else 0 }
    return JsonResponse(resp, status = 200)
  except CreatorInfo.DoesNotExist:
    return JsonResponse({ "error": "Data does not exist." }, status = 404)
  
@csrf_exempt
def get_history(request):
  if request.method != "GET":
    return JsonResponse({ "error": 'Invalid request type.'}, 501)
  
  weekday_str : str = request.GET.get("weekday", None)
  year_str    : str = request.GET.get("year", None)
  month_str   : str = request.GET.get("month", None)
  
  weekday_filter = None
  if weekday_str is not None:
    weekdaystr = weekday_str.lower()
    if weekdaystr in ['m', 'mon', 'monday', '0']:
      weekday_filter = Weekday.MON
    elif weekdaystr in ['t', 'tues', 'tuesday', '1']:
      weekday_filter = Weekday.TUE
    elif weekdaystr in ['w', 'wed', 'wednesday', '2']:
      weekday_filter = Weekday.WED
    elif weekdaystr in ['th', 'thurs', 'thursday', '3']:
      weekday_filter = Weekday.THU
    elif weekdaystr in ['f', 'fri', 'friday', '4']:
      weekday_filter = Weekday.FRI
    elif weekdaystr in ['s', 'sat', 'saturday', '5']:
      weekday_filter = Weekday.SAT
    elif weekdaystr in ['su', 'sun', 'sunday', '6']:
      weekday_filter = Weekday.SUN
  
  year_filter = None
  if year_str is not None:
    if year_str.isdigit() and len(year_str) == 4:
      year_filter = year_str
      
  month_filter = None
  if month_str is not None:
    if month_str.isdigit() and len(month_str) < 3:
      month_filter = month_str.rjust(2, "0")
  
  streaminfo_list = StreamInfo.objects.all().order_by('date')
  
  if year_filter is not None and month_filter is not None:
    combofilter = year_filter + month_filter
    streaminfo_list = streaminfo_list.filter(date__startswith = combofilter)
  elif year_filter is not None:
    streaminfo_list = streaminfo_list.filter(date__startswith = year_filter)
  elif month_filter is not None:
    streaminfo_list = streaminfo_list.filter(date__iregex = rf"^[0-9]{{4}}({month_filter})[0-9]{{2}}$")
    
  if weekday_filter is not None:
    streaminfo_list = streaminfo_list.filter(weekday = weekday_filter)
      
  resp = { "streams": { } }
  
  for streaminfo in streaminfo_list:
    stream_date = streaminfo.get_pretty_date()
  
    resp["streams"][stream_date] = streaminfo.to_dict()
    
  return JsonResponse(resp, status = 200)

@csrf_exempt
def get_when_live(request):
  if request.method != "GET":
    return JsonResponse({ "error": 'Invalid request type.'}, 501)
  
  try:
    creatorinfo = CreatorInfo.objects.get(creator_id = CREATOR_ID)
    
    delta = dt.timedelta(seconds = creatorinfo.average_offset)
    average_time = (dt.datetime.combine(dt.date.today(), GOAL_TIME) + delta)
    resp = { "average": average_time.strftime("%I:%M:%S %p") }
    
    return JsonResponse(resp, status = 200)
  except CreatorInfo.DoesNotExist:
    return JsonResponse({ "error": "Data does not exist." }, status = 404)

@csrf_exempt
def get_streaks(request):
  if request.method != "GET":
    return JsonResponse({ "error": 'Invalid request type.'}, 501)
  
  try:
    creatorinfo = CreatorInfo.objects.get(creator_id = CREATOR_ID)
    
    resp = { 
      "early": creatorinfo.longest_early_streak,
      "on-time": creatorinfo.longest_ontime_streak,
      "late": creatorinfo.longest_late_streak,        
    }
    
    return JsonResponse(resp, status = 200)
  except CreatorInfo.DoesNotExist:
    return JsonResponse({ "error": "Data does not exist." }, status = 404)