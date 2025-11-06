from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_simulation, name='start_simulation'),
    path('data/', views.carrefour_data, name='carrefour_data'),
]
