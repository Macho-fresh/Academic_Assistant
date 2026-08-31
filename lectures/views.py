from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from indexing.services import generate_topics
from courses.models import Course
from transcription.services import transcribe_audio
from summary.services import save_lecture_summary
from .models import *


@login_required(login_url="login")
def lectures_view(request):

    query = request.GET.get("q", "").strip()

    if request.user.role == "lecturer":
        lectures = (
            Lecture.objects
            .filter(course__lecturer=request.user)
            .select_related("course", "lecturer")
            .order_by("-id")
        )

    else:
        lectures = (
            Lecture.objects
            .select_related("course", "lecturer")
            .order_by("-id")
        )

    if query:
        lectures = lectures.filter(
            Q(title__icontains=query)
            | Q(course__course_code__icontains=query)
            | Q(course__course_title__icontains=query)
        )

    context = {
        "lectures": lectures,
        "query": query,
    }

    return render(
        request,
        "lectures/lecture_list.html",
        context
    )


@login_required(login_url="login")
def lecture_detail(request, lecture_id):

    lecture = get_object_or_404(
        Lecture.objects.select_related(
            "course",
            "lecturer"
        ),
        id=lecture_id
    )

    transcript_segments = (
        TranscriptSegment.objects
        .filter(lecture=lecture)
        .order_by("start_seconds")
    )

    topic_segments = (
        TopicSegment.objects
        .filter(lecture=lecture)
        .order_by("start_seconds")
    )

    summary = (
        LectureSummary.objects
        .filter(lecture=lecture)
        .first()
    )

    print("SUMMARY OBJECT:", summary)

    if summary:
        print("SUMMARY TEXT:", summary.summary_text)
        print("KEY POINTS:", summary.key_points)

    context = {
        "lecture": lecture,
        "transcript_segments": transcript_segments,
        "topic_segments": topic_segments,
        "summary": summary,
    }

    return render(
        request,
        "lectures/lecture_detail.html",
        context
    )

def save_transcript_segments(lecture, segments):

    TranscriptSegment.objects.filter(
        lecture=lecture
    ).delete()

    transcript_objects = []

    for segment in segments:

        transcript_objects.append(
            TranscriptSegment(
                lecture=lecture,
                start_seconds=segment["start"],
                end_seconds=segment["end"],
                text=segment["text"]
            )
        )

    TranscriptSegment.objects.bulk_create(
        transcript_objects
    )


def process_lecture_transcription(lecture):

    lecture.status = "processing"

    lecture.save(
        update_fields=["status"]
    )

    try:

        print("Step 1: Transcribing audio")

        result = transcribe_audio(
            lecture.audio_file.path
        )

        lecture.transcript = result["text"]

        lecture.save(
            update_fields=["transcript"]
        )


        print("Step 2: Saving transcript segments")

        save_transcript_segments(
            lecture,
            result["segments"]
        )


        print("Step 3: Generating topics")

        generate_topics(
            lecture
        )


        print("Step 4: Generating summary")

        save_lecture_summary(
            lecture
        )


        print("Step 5: Processing completed")

        lecture.status = "completed"

        lecture.save(
            update_fields=["status"]
        )

        return True, None


    except Exception as error:

        print(
            f"Lecture processing failed for lecture {lecture.id}:",
            error
        )

        lecture.status = "failed"

        lecture.save(
            update_fields=["status"]
        )

        return False, error

    lecture.status = "processing"

    lecture.save(
        update_fields=["status"]
    )

    try:

        # STEP 1: Transcribe audio
        result = transcribe_audio(
            lecture.audio_file.path
        )

        lecture.transcript = result["text"]

        # STEP 2: Save timestamped transcript
        save_transcript_segments(
            lecture,
            result["segments"]
        )

        # STEP 3: Generate lecture topics
        generate_topics(
            lecture
        )

        # We will add summary generation here next

        lecture.status = "completed"

        lecture.save(
            update_fields=[
                "transcript",
                "status"
            ]
        )

        return True, None

    except Exception as error:

        print(
            f"Lecture processing failed for lecture {lecture.id}:",
            error
        )

        lecture.status = "failed"

        lecture.save(
            update_fields=["status"]
        )

        return False, error

    lecture.status = "processing"

    lecture.save(
        update_fields=["status"]
    )

    try:

        result = transcribe_audio(
            lecture.audio_file.path
        )

        lecture.transcript = result["text"]

        save_transcript_segments(
            lecture,
            result["segments"]
        )

        lecture.status = "completed"

        lecture.save(
            update_fields=[
                "transcript",
                "status"
            ]
        )

        return True, None

    except Exception as error:

        print(
            f"Transcription failed for lecture {lecture.id}:",
            error
        )

        lecture.status = "failed"

        lecture.save(
            update_fields=["status"]
        )

        return False, error


class RecordLectureView(LoginRequiredMixin, View):

    login_url = "login"

    def get(self, request):

        if request.user.role != "lecturer":

            messages.error(
                request,
                "Only lecturers can record lectures."
            )

            return redirect(
                "lectures"
            )

        courses = Course.objects.filter(
            lecturer=request.user
        ).order_by("course_code")

        selected_course = None

        course_id = request.GET.get(
            "course"
        )

        if course_id:

            selected_course = get_object_or_404(
                Course,
                id=course_id,
                lecturer=request.user
            )

        return render(
            request,
            "lectures/record.html",
            {
                "courses": courses,
                "selected_course": selected_course,
            }
        )

    def post(self, request):

        if request.user.role != "lecturer":

            messages.error(
                request,
                "Only lecturers can record lectures."
            )

            return redirect(
                "lectures"
            )

        title = request.POST.get(
            "title",
            ""
        ).strip()

        course_id = request.POST.get(
            "course"
        )

        audio_file = request.FILES.get(
            "audio_file"
        )

        if not title:

            messages.error(
                request,
                "Lecture title is required."
            )

            return redirect(
                "record_lecture"
            )

        if not course_id:

            messages.error(
                request,
                "Please select a course."
            )

            return redirect(
                "record_lecture"
            )

        if not audio_file:

            messages.error(
                request,
                "No recording was received."
            )

            return redirect(
                "record_lecture"
            )

        course = get_object_or_404(
            Course,
            id=course_id,
            lecturer=request.user
        )

        lecture = Lecture.objects.create(
            course=course,
            title=title,
            lecturer=request.user,
            audio_file=audio_file,
            status="pending"
        )

        success, error = process_lecture_transcription(
            lecture
        )

        if success:

            messages.success(
                request,
                "Lecture recorded and transcribed successfully."
            )

        else:

            messages.error(
                request,
                "Lecture was saved, but transcription failed."
            )

        return redirect(
            "lecture_detail",
            lecture_id=lecture.id
        )


@login_required(login_url="login")
def retry_processing(request, lecture_id):

    lecture = get_object_or_404(
        Lecture.objects.select_related(
            "lecturer"
        ),
        id=lecture_id
    )

    if request.method != "POST":

        return redirect(
            "lecture_detail",
            lecture_id=lecture.id
        )

    if (
        request.user.role != "lecturer"
        or lecture.lecturer != request.user
    ):

        messages.error(
            request,
            "You do not have permission to process this lecture."
        )

        return redirect(
            "lecture_detail",
            lecture_id=lecture.id
        )

    if not lecture.audio_file:

        messages.error(
            request,
            "This lecture does not have an audio recording."
        )

        return redirect(
            "lecture_detail",
            lecture_id=lecture.id
        )

    success, error = process_lecture_transcription(
        lecture
    )

    if success:

        messages.success(
            request,
            "Lecture processed successfully."
        )

    else:

        messages.error(
            request,
            "Lecture processing failed again."
        )

    return redirect(
        "lecture_detail",
        lecture_id=lecture.id
    )