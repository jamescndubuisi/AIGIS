from django.urls import path
from .views import login_page, homepage, sign_up, upload_data, DataListView, DataDetailView, DataUpdateView,DataDeleteView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('login', login_page, name='log_in'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('', homepage, name="home"),
    path('register', sign_up, name="register"),
    path('upload', upload_data, name="upload"),
    path('data', DataListView.as_view(), name="list"),
    path('data/<str:pk>', DataDetailView.as_view(), name="detail"),
    path('update/<str:pk>', DataUpdateView.as_view(), name="update"),
    path('delete/<str:pk>', DataDeleteView.as_view(), name="delete"),
]


