from django.urls import path
from . import views

urlpatterns = [
    path('mgjfrontend/', views.mgjfrontend, name='mjgfrontend'),
]