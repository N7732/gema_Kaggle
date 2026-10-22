"""
URL configuration for CodeGuardian project.
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from issues.views import IssueViewSet
from patches.views import PatchViewSet
from experiments.views import ExperimentViewSet

router = DefaultRouter()
router.register(r'issues', IssueViewSet, basename='issue')
router.register(r'patches', PatchViewSet, basename='patch')
router.register(r'experiments', ExperimentViewSet, basename='experiment')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),

    # OpenAPI 3 Schema & Swagger UI
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
