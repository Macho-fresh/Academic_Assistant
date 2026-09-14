from django.urls import path

from .views import (
    AssistantView,
    AskAssistantView,
)


urlpatterns = [

    path(
        "assistant/",
        AssistantView.as_view(),
        name="assistant"
    ),

    path(
        "ask/",
        AskAssistantView.as_view(),
        name="ask_assistant"
    ),

]