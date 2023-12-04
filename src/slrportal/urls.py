from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('logout', views.logout_view, name='logout'),
    path('profile', views.profile_view, name='profile'),
    path('privacy-policy', views.privacy_policy, name='privacy_policy'),
    path('accept-cookies', views.accept_cookies, name='accept_cookies'),
    path('s/<str:short_url>', views.redirect_url, name='redirect'),
    path('next-party/', views.get_next_party, name='next_party'),
    path('party/<str:edition>', views.party_detail, name='party'),
    path('item/<str:item_id>/assign/<str:person_id>', views.assign_item, name='assign_item'),
    path('item/<str:item_id>/unassign/<str:person_id>', views.unassign_item, name='unassign_item'),
    path('party/<str:edition>/add-item', views.add_item, name='add_item'),
    path('party/<str:edition>/rsvp', views.update_rsvp, name='update_rsvp'),
    path('add-allergy', views.add_allergy, name='add_allergy'),
    path('delete-allergy/<int:allergy_id>', views.delete_allergy, name='delete_allergy'),
]
