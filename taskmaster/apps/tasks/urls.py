from django.urls import path
from .views import (
    TaskListView, TaskCreateView, TaskUpdateView,
    TaskDeleteView, TaskCompleteView, TaskStopRepeatView,
    category_create, category_update, category_delete
)

app_name = 'tasks'

urlpatterns = [
    path('', TaskListView.as_view(), name='list'),
    path('create/', TaskCreateView.as_view(), name='create'),
    path('<int:pk>/edit/', TaskUpdateView.as_view(), name='edit'),
    path('<int:pk>/delete/', TaskDeleteView.as_view(), name='delete'),
    path('<int:pk>/complete/', TaskCompleteView.as_view(), name='complete'),
    path('<int:pk>/stop-repeat/', TaskStopRepeatView.as_view(), name='stop_repeat'),
    path('categories/create/', category_create, name='category_create'),
    path('categories/<int:pk>/update/', category_update, name='category_update'),
    path('categories/<int:pk>/delete/', category_delete, name='category_delete'),
]
