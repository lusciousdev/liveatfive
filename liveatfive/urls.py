from django.urls import path

from . import views
from . import api

app_name = 'liveatfive'
urlpatterns = [
  path("", views.IndexView.as_view(), name="index"),
  path("faq", views.FAQView.as_view(), name="faq"),
  path("stats", views.StatsView.as_view(), name="stats"),
  path("api/v1/record", api.get_record, name="api_record"),
  path("api/v1/live", api.get_is_live, name="api_live"),
  path("api/v1/history", api.get_history, name="api_history"),
  path("api/v1/when", api.get_when_live, name="api_when"),
  path("api/v1/streaks", api.get_streaks, name="api_streaks"),
]