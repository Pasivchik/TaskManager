from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.tasks.views import DashboardView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', DashboardView.as_view(), name='dashboard'),
    path('accounts/', include('apps.accounts.urls')),
    path('tasks/', include('apps.tasks.urls')),
    path('gamification/', include('apps.gamification.urls')),
    path('shop/', include('apps.shop.urls')),
    path('stats/', include('apps.stats.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
