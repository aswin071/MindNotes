from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    ChangePasswordView,
    LogoutView,
    RefreshTokenWrappedView,
    GoogleSignInView,
    GoogleSignupView,
    DashboardView,
)

urlpatterns = [
    # Email flows
    path('signup', RegisterView.as_view(),                                                          name='auth-signup-email'),
    path('login', LoginView.as_view(),                                                              name='auth-login-email'),
    path('refresh', RefreshTokenWrappedView.as_view(),                                              name='auth-refresh'),
    path('profile', ProfileView.as_view(),                                                          name='auth-profile'),
    path('change-password', ChangePasswordView.as_view(),                                           name='auth-change-password'),
    path('logout', LogoutView.as_view(),                                                            name='auth-logout'),
    # Google flows
    path('signup/google', GoogleSignupView.as_view(),                                               name='auth-signup-google'),
    path('login/google', GoogleSignInView.as_view(),                                                name='auth-login-google'),

    # Home Page
    path('home', DashboardView.as_view(),                                                           name='home'),
]


