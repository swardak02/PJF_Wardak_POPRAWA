from django.urls import path, include
from . import views

urlpatterns = [
    path('login/', views.loginPage, name="login"),
    path('logout/', views.logoutUser, name="logout"),
    path('register/', views.registerPage, name="register"),

    path('calendar/', views.CalendarView.as_view(), name='calendar'),
    path('calendar/filter', views.CalendarView.as_view(), name='calendar_filter'),
    path('calendar_event/new/', views.calendar_event, name='calendar_event_new'),
    path('calendar_event/edit/(<str:event_id>)/', views.calendar_event, name='calendar_event_edit'),
    path('calendar_event/delete/(<str:event_id>)',views.calendar_event_delete, name='calendar_event_delete'),

    path('', views.home, name="home"),
    path('offer/<str:pk>', views.offer, name="offer"),
    path('profile/<str:pk>/', views.userProfile, name="user-profile"),

    path('create-offer/', views.createOffer, name="create-offer"),
    path('update-offer/<str:pk>/', views.updateOffer, name="update-offer"),
    path('delete-offer/<str:pk>/', views.deleteOffer, name="delete-offer"),

    path('update-user/', views.updateUser, name="update-user"),

]