from django.urls import path

from .views import *

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

    path(
        "clear-chat/",
        ClearChatView.as_view(),
        name="clear_chat"
    ),

]