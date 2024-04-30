from django.test import TestCase
from .models import *

# Create your tests here.
class StreamInfoTestCase(TestCase):
  def setUp(self):
    si = StreamInfo.objects.create_streaminfo(date = "20240101", start_time = datetime.datetime(2024, 1, 2, 1, 15, 59, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    si = StreamInfo.objects.create_streaminfo(date = "20240102", start_time = datetime.datetime(2024, 1, 3, 1, 15, 59, 1).replace(tzinfo = datetime.timezone.utc))
    si.save()
    
    si = StreamInfo.objects.create_streaminfo(date = "20240103", start_time = datetime.datetime(2024, 1, 4, 1, 30, 0, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    si = StreamInfo.objects.create_streaminfo(date = "20240104", start_time = datetime.datetime(2024, 1, 5, 1, 16, 0, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    
    si = StreamInfo.objects.create_streaminfo(date = "20240105", start_time = datetime.datetime(2024, 1, 6, 1,  0,  0, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    si = StreamInfo.objects.create_streaminfo(date = "20240106", start_time = datetime.datetime(2024, 1, 7, 0, 45, 59, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    
    si = StreamInfo.objects.create_streaminfo(date = "20240107", start_time = datetime.datetime(2024, 1, 8, 0, 44, 59, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    si = StreamInfo.objects.create_streaminfo(date = "20240108", start_time = datetime.datetime(2024, 1, 9, 0,  0,  0, 0).replace(tzinfo = datetime.timezone.utc))
    si.save()
    
  def test_streaminfo_punctuality(self):
    dt1 = StreamInfo.objects.get(date = "20240101")
    dt2 = StreamInfo.objects.get(date = "20240102")
    dt3 = StreamInfo.objects.get(date = "20240103")
    dt4 = StreamInfo.objects.get(date = "20240104")
    dt5 = StreamInfo.objects.get(date = "20240105")
    dt6 = StreamInfo.objects.get(date = "20240106")
    dt7 = StreamInfo.objects.get(date = "20240107")
    dt8 = StreamInfo.objects.get(date = "20240108")
    
    self.assertTrue(dt1.punctuality == Punctuality.ONTIME)
    self.assertTrue(dt2.punctuality == Punctuality.ONTIME)
    
    self.assertTrue(dt3.punctuality == Punctuality.LATE)
    self.assertTrue(dt4.punctuality == Punctuality.LATE)
    
    self.assertTrue(dt5.punctuality == Punctuality.ONTIME)
    self.assertTrue(dt6.punctuality == Punctuality.ONTIME)
    
    self.assertTrue(dt7.punctuality == Punctuality.EARLY)
    self.assertTrue(dt8.punctuality == Punctuality.EARLY)
    