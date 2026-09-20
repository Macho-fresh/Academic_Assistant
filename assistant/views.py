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
            data = json.loads(request.body)

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

        # Save user's message
        AssistantMessage.objects.create(
            user=request.user,
            role="user",
            message=query
        )

        # Generate the assistant result
        result = answer_question(
            request.user,
            query
        )

        # Save assistant response + result information
        AssistantMessage.objects.create(
            user=request.user,
            role="assistant",
            message=result["answer"],
            metadata={
                "lecture": result.get("lecture"),
                "course": result.get("course"),
                "lecture_id": result.get("lecture_id"),
                "timestamp": result.get("timestamp"),
                "timestamp_display": result.get(
                    "timestamp_display"
                ),
                "match_type": result.get("match_type"),
            }
        )

        # Send the result back to JavaScript
        return JsonResponse(result)
    
class ClearChatView(LoginRequiredMixin, View):

    login_url = "login"

    def post(self, request):

        AssistantMessage.objects.filter(
            user=request.user
        ).delete()

        return JsonResponse({
            "message": "Chat cleared."
        })

