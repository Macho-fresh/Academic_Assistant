from django.contrib import admin
from .models import *

admin.site.register(Lecture)
admin.site.register(TranscriptSegment)
admin.site.register(TopicSegment)
admin.site.register(LectureSummary)