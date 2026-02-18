from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, api

router = DefaultRouter()
router.register(r'schedules', api.VesselScheduleViewSet, basename='vessel-schedule')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/autocomplete/port/', api.AutocompleteViewSet.as_view({'get': 'port'}), name='api-autocomplete-port'),
    path('api/autocomplete/vessel/', api.AutocompleteViewSet.as_view({'get': 'vessel'}), name='api-autocomplete-vessel'),
    path('api/autocomplete/operator/', api.AutocompleteViewSet.as_view({'get': 'operator'}), name='api-autocomplete-operator'),
    path('api/upload/', api.UploadScheduleAPIView.as_view(), name='api-upload-schedule'),
    
    # Existing routes
    path('api/schedule/', views.schedule_api, name='schedule_api'),
    path('dashboard/', views.ScheduleDashboardView.as_view(), name='schedule_dashboard'),
    path('search/', views.search_schedule_view, name='search_schedule'),
    path('upload_schedule/', views.upload_schedule_view, name='upload_schedule'),
]
