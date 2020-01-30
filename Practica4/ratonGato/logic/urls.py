from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index, name='landing'),
    path('index/', views.index, name='index'),
    path('login_service/', views.login_service, name='login'),
    path('logout_service/', views.logout_service, name='logout'),
    path('signup_service/', views.signup_service, name='signup'),
    path('create_game_service/', views.create_game_service, name='create_game'),
    path('join_game_service/<int:game_id>/', views.join_game_service, name='join_game'),
    path('select_join/', views.select_join_service, name='select_join'),
    path('select_view/', views.select_view_service, name='select_view'),
    path('select_game_service/', views.select_game_service, name='select_game'),
    path('select_game/<int:game_id>/', views.select_game_service, name='select_game'),
    path('show_game_service/', views.show_game_service, name='show_game'),
    path('move_service/', views.move_service, name='move'),
    path('play_game_service/get_moves_service/<int:shift>/', views.get_moves_service, name='get_moves_service'),
    path('select_game/<int:game_id>/get_moves_service/<int:shift>/', views.get_moves_service, name='get_moves_service'),
    path('show_game_service/load_board/<int:gameid>/', views.load_board, name='load_board'),
    path('move_service/load_board/<int:gameid>/', views.load_board, name='load_board'),
    path('play_game_service/', views.play_game_service, name='play_game')
]
