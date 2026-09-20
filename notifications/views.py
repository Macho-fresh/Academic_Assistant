from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View

from .models import Notification


class UnreadNotificationsView(
    LoginRequiredMixin,
    View
):

    login_url = "login"

    def get(self, request):

        notifications = (
            Notification.objects
            .filter(
                user=request.user,
                is_read=False
            )
            .order_by("created_at")
        )

        data = []

        for notification in notifications:

            data.append({
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
            })

        return JsonResponse({
            "notifications": data
        })

class MarkNotificationReadView(
    LoginRequiredMixin,
    View
):

    login_url = "login"

    def post(
        self,
        request,
        notification_id
    ):

        notification = (
            Notification.objects
            .filter(
                id=notification_id,
                user=request.user
            )
            .first()
        )

        if not notification:

            return JsonResponse(
                {
                    "error":
                    "Notification not found."
                },
                status=404
            )

        notification.is_read = True

        notification.save(
            update_fields=["is_read"]
        )

        return JsonResponse({
            "success": True
        })