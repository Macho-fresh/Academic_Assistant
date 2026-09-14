from django.shortcuts import render
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
import json

from .services import answer_question
from .models import AssistantMessage

class AssistantView(LoginRequiredMixin, View):

    login_url = "login"

    def get(self, request):

        messages = AssistantMessage.objects.filter(
            user=request.user
        ).order_by("created_at")

        return render(
            request,
            "assistant/assistant.html",
            {
                "assistant_messages": messages,
                "active_nav": "assistant",
            }
        )


class AskAssistantView(LoginRequiredMixin, View):

    login_url = "login"

    def post(self, request):

        try:
            data = json.loads(
                request.body
            )

            query = data.get(
                "message",
                ""
            ).strip()

        except json.JSONDecodeError:

            return JsonResponse(
                {
                    "error": "Invalid request."
                },
                status=400
            )

        if not query:

            return JsonResponse(
                {
                    "error": "Please enter a question."
                },
                status=400
            )

        AssistantMessage.objects.create(
            user=request.user,
            role="user",
            message=query
        )

        result = answer_question(
            request.user,
            query
        )

        AssistantMessage.objects.create(
            user=request.user,
            role="assistant",
            message=result["answer"]
        )

        return JsonResponse(result)