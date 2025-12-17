from django.urls import path
from . import views

urlpatterns = [
    path('', 
        views.index, 
        name='index'),

    path('start/', 
        views.start_simulation, name='start_simulation'),

    path('stop/', 
        views.stop_simulation, name='stop_simulation'),

    path('statistics/', 
        views.get_all_statistics, name='get_all_statistics'),

    path('statistic/delete/<int:id>/', 
        views.delete_statistic, name='delete_statistic'),

    path('statistic/filter/date/', views.get_statistics_by_date, name='get_statistics_by_date'),


    path('data/', 
        views.carrefour_data, name='carrefour_data'),

    path('traffic_light/stop_all', 
        views.stop_all_tl, name='stop_all_traffic'),

    path('traffic_light/restore_controle', 
        views.restore_controle_tl, name='restore_controle'),

    path('traffic_light/prioritize/<int:lane>/', 
        views.prioritize_lane, name='prioritize_lane'),

    path('traffic_light/prioritize_direction/<str:direction>/',
        views.prioritize_lane_by_direction, name='prioritize_lane_by_direction'),

    path('traffic_light/change_phase/<int:phase_index>/<int:duration>/',
        views.change_phase_duration,
        name='change_phase_duration'
    ),

    path('vehicle/create/<str:vehicleID>/<str:routeID>/',
        views.create_vehicle,
        name='create_vehicle'
    ),

    path('traffic_light/change_phase/yellow/<int:duration>/',
        views.change_phase_duration_by_group_yellow,
        name='change_phase_duration'
    ),

    path('traffic_light/change_phase/green_main/<int:duration>/',
        views.change_phase_duration_by_group_green_main,
        name='change_phase_duration'
    ),

    path('traffic_light/change_phase/green_short/<int:duration>/',
        views.change_phase_duration_by_group_green_short,
        name='change_phase_duration'
    ),
]