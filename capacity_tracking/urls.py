from django.urls import path
from . import views

urlpatterns = [
    path('api/schedule/', views.schedule_api, name='schedule_api'),
    path('dashboard/', views.ScheduleDashboardView.as_view(), name='schedule_dashboard'),
    path('search/', views.search_schedule_view, name='search_schedule'),
    path('api/autocomplete/port/', views.autocomplete_port, name='autocomplete_port'),
    path('api/autocomplete/vessel/', views.autocomplete_vessel_schedule, name='autocomplete_vessel'),
    path('api/autocomplete/operator/', views.autocomplete_operator, name='autocomplete_operator'),
    path('upload_schedule/', views.upload_schedule_view, name='upload_schedule'),
]
