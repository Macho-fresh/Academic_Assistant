from django.urls import path
from . import views

urlpatterns = [
    path("lectures/", views.lectures_view, name="lectures"),
    path("lecture-detail/<int:lecture_id>", views.lecture_detail, name="lecture_detail"),
    path("record-lecture/", views.RecordLectureView.as_view(), name="record_lecture"),
    path(
    "lecture/<int:lecture_id>/retry/",
    views.retry_processing,
    name="retry_processing"
),
]