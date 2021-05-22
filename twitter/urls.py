from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from accounts.api import views

router = routers.DefaultRouter()
router.register(r'api/users', views.UserViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls',
namespace='rest_framework')),
]