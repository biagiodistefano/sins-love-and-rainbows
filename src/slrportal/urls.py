from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('s/<str:short_url>', views.redirect_url, name='redirect'),
    path('next-party/', views.get_next_party, name='next_party'),
    path('party/<str:edition>', views.party_detail, name='party'),
    path('item/<str:item_id>/assign/<str:person_id>', views.assign_item, name='assign_item'),
    path('item/<str:item_id>/unassign/<str:person_id>', views.unassign_item, name='unassign_item'),
    path('party/<str:edition>/add-item', views.add_item, name='add_item'),
]
