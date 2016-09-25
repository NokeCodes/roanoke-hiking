from django.conf.urls import url

from .views import hikes


urlpatterns = [
    url(r'^hikes/', hikes),
]
