from django.urls import path

from routing.views import LocationSearchView, RoutePlanView

app_name = 'routing'

urlpatterns = [
    path('locations/', LocationSearchView.as_view(), name='location-search'),
    path('route-plans/', RoutePlanView.as_view(), name='route-plan'),
]
