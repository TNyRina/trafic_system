from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('start/', views.start_simulation, name='start_simulation'),
    path('data/', views.carrefour_data, name='carrefour_data'),
    path('traffic_light/stop_all', views.stop_all_tl, name='stop_all_traffic'),
    path('traffic_light/restore_controle', views.restore_controle_tl, name='restore_controle'),
]
