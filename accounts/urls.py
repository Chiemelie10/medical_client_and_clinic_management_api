from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import AuthView, CustomTokenRefreshView


router = SimpleRouter()
router.register("", AuthView, basename="account")

urlpatterns = [
    path(
        "token/refresh/", CustomTokenRefreshView.as_view(), name="token_refresh",
    ),
]

urlpatterns += router.urls
