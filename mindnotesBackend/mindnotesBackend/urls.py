"""mindnotesBackend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import (
    include,
    path
)
from core.views import health_check, readiness_check, liveness_check

urlpatterns = [
    # Health checks (unauthenticated for load balancers)
    path('health/', health_check, name='health_check'),
    path('ready/', readiness_check, name='readiness_check'),
    path('alive/', liveness_check, name='liveness_check'),

    # Admin
    path('admin-site-mindnotes/', admin.site.urls),

    # API endpoints
    path('api/v1/authentication/', include('api.v1.authentication.urls')),
    path('api/v1/journals/', include('api.v1.journals.urls')),
    path('api/v1/focus/', include('api.v1.focus.urls')),
    path('api/v1/prompts/', include('api.v1.prompts.urls')),
    path('api/v1/analytics/', include('api.v1.analytics.urls')),
    path('api/v1/moods/', include('api.v1.moods.urls')),
    path('api/v1/subscriptions/', include('api.v1.subscriptions.urls')),
    path('api/v1/exports/', include('api.v1.exports.urls')),
]
