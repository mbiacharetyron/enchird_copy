"""
URL configuration for enchird_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

from django.urls import path, include
from rest_framework import routers
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from apis.users.views import EmailVerificationView
from apis.users.reset_password import ResetPasswordView



app_name = 'api'
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('apis.students.urls')),  # This includes the student app's URLs under /api/
    path('api/', include('apis.applicants.urls')),
    path('api/', include('apis.assessment.urls')),
    path('api/', include('apis.messaging.urls')),
    path('api/', include('apis.payments.urls')),
    path('api/', include('apis.teachers.urls')),
    path('api/', include('apis.courses.urls')),
    path('api/', include('apis.faculty.urls')),
    path('api/', include('apis.users.urls')),
    path('paypal/', include('paypal.standard.ipn.urls')),
    path('verify-email/<verification_token>/', EmailVerificationView.as_view(), name="verify-email"),
    path('reset-password/', ResetPasswordView.as_view(), name="reset-password"),
    # path('api/', include((router.urls, 'api'))),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

