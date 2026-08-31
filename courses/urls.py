from django.urls import path
from .views import *

urlpatterns = [
    path("courses/", course_list, name="courses"),
    path("add-course/", AddCourseView.as_view(), name="add_course"),
    path("course-detail/<int:course_id>", course_detail, name="course_detail")
]