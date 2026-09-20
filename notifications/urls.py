from django.urls import path

from .views import (
    UnreadNotificationsView,
    MarkNotificationReadView,
)


urlpatterns = [

    path(
        "unread/",
        UnreadNotificationsView.as_view(),
        name="unread_notifications"
    ),

    path(
        "notification/<int:notification_id>/read/",
        MarkNotificationReadView.as_view(),
        name="mark_notification_read"
    ),

]