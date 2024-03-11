from .logout import Logout
from django.urls import path
from .login import LoginView
from .views import *
from apis.users.login import *
from knox import views as knox_views
from django.urls import path, include
from apis.users.reset_password import *
from .change_password import ChangePasswordView
from rest_framework.routers import DefaultRouter


# Create a router
router = DefaultRouter()

# Register the ProductViewSet with a base name 'product'
# router.register(r'login', CustomTokenObtainPairView.as_view(), basename="login")

urlpatterns = [
    path('', include(router.urls)),
    path('auth/login/', LoginView.as_view(), name='Login'),
    path('auth/logout/', knox_views.LogoutView.as_view(), name='Logout'),
    path('admin/search/', admin_general_search, name='admin_general_search'),
    path('tutor-search/', tutor_general_search, name='tutor_general_search'),
    path('auth/logoutall/', knox_views.LogoutAllView.as_view(), name="Logout all sessions"),
    path('verify-email/<verification_token>/', EmailVerificationView.as_view(), name="verify-email"),
    path('reset_password/<verification_token>/', ResetPasswordView.as_view(), name="verify-email"),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
]