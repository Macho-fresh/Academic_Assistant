from django.urls import path
from .views import *

urlpatterns = [
    path(
        "",
        TimetableView.as_view(),
        name="timetable"
    ),

    path(
        "add/",
        AddClassView.as_view(),
        name="add_class"
    ),

    path(
        "delete/<int:entry_id>/",
        DeleteClassView.as_view(),
        name="delete_class"
    ),
]