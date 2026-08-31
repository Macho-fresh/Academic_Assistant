from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from indexing.services import generate_topics
from courses.models import Course
from transcription.services import transcribe_audio, make_audio_seekable
from summary.services import save_lecture_summary
from .models import *


@login_required(login_url="login")
def lectures_view(request):

    query = request.GET.get("q", "").strip()
    course_id = request.GET.get("course", "").strip()
    date_filter = request.GET.get("date", "").strip()
    status_filter = request.GET.get("status", "").strip()


    # ==========================================
    # BASE LECTURES
    # ==========================================

    if request.user.role == "lecturer":

        lectures = (
            Lecture.objects
            .filter(lecturer=request.user)
            .select_related(
                "course",
                "lecturer"
            )
        )

        courses = Course.objects.filter(
            lecturer=request.user
        ).order_by("course_code")

    else:

        lectures = (
            Lecture.objects
            .select_related(
                "course",
                "lecturer"
            )
        )

        courses = Course.objects.all().order_by(
            "course_code"
        )


    # ==========================================
    # SEARCH
    # ==========================================

    if query:

        lectures = lectures.filter(
            Q(title__icontains=query)
            | Q(course__course_code__icontains=query)
            | Q(course__course_title__icontains=query)
            | Q(lecturer__first_name__icontains=query)
            | Q(lecturer__last_name__icontains=query)
        )


    # ==========================================
    # COURSE FILTER
    # ==========================================

    if course_id:

        lectures = lectures.filter(
            course_id=course_id
        )


    # ==========================================
    # STATUS FILTER
    # ==========================================

    valid_statuses = [
        "pending",
        "processing",
        "completed",
        "failed",
    ]

    if status_filter in valid_statuses:

        lectures = lectures.filter(
            status=status_filter
        )


    # ==========================================
    # DATE FILTER / SORTING
    # ==========================================

    if date_filter == "oldest":

        lectures = lectures.order_by(
            "created_at"
        )

    elif date_filter == "today":

        from django.utils import timezone

        lectures = lectures.filter(
            created_at__date=timezone.localdate()
        ).order_by(
            "-created_at"
        )

    elif date_filter == "week":

        from datetime import timedelta
        from django.utils import timezone

        seven_days_ago = (
            timezone.now()
            - timedelta(days=7)
        )

        lectures = lectures.filter(
            created_at__gte=seven_days_ago
        ).order_by(
            "-created_at"
        )

    else:

        # Default = newest first
        lectures = lectures.order_by(
            "-created_at"
        )


    context = {
        "lectures": lectures,
        "courses": courses,

        "query": query,
        "selected_course": course_id,
        "selected_date": date_filter,
        "selected_status": status_filter,
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

        make_audio_seekable(lecture.audio_file.path)
        # lecture.duration_seconds = (
        #     get_audio_duration(
        #         lecture.audio_file.path
        #     )
        # )

        # lecture.save(
        #     update_fields=[
        #         "duration_seconds"
        #     ]
        # )

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

@login_required(login_url="login")
def delete_lecture(request, lecture_id):

    lecture = get_object_or_404(
        Lecture,
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
            "You do not have permission to delete this lecture."
        )

        return redirect(
            "lecture_detail",
            lecture_id=lecture.id
        )

    course_id = lecture.course.id

    lecture.delete()

    messages.success(
        request,
        "Lecture deleted successfully."
    )

    return redirect(
        "course_detail",
        course_id=course_id
    )

class UploadLectureView(LoginRequiredMixin, View):

    login_url = "login"

    def get(self, request):

        if request.user.role != "lecturer":

            messages.error(
                request,
                "Only lecturers can upload lectures."
            )

            return redirect(
                "lectures"
            )


        courses = Course.objects.filter(
            lecturer=request.user
        ).order_by("course_code")


        selected_course = None

        course_id = request.GET.get("course")


        if course_id:

            selected_course = get_object_or_404(
                Course,
                id=course_id,
                lecturer=request.user
            )


        return render(
            request,
            "lectures/upload.html",
            {
                "courses": courses,
                "selected_course": selected_course,
            }
        )


    def post(self, request):

        if request.user.role != "lecturer":

            messages.error(
                request,
                "Only lecturers can upload lectures."
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
                "upload_lecture"
            )


        if not course_id:

            messages.error(
                request,
                "Please select a course."
            )

            return redirect(
                "upload_lecture"
            )


        if not audio_file:

            messages.error(
                request,
                "Please select an audio file."
            )

            return redirect(
                "upload_lecture"
            )


        allowed_extensions = (
            ".mp3",
            ".wav",
            ".m4a",
            ".webm",
            ".ogg",
        )


        filename = audio_file.name.lower()


        if not filename.endswith(
            allowed_extensions
        ):

            messages.error(
                request,
                "Unsupported audio format."
            )

            return redirect(
                "upload_lecture"
            )


        course = get_object_or_404(
            Course,
            id=course_id,
            lecturer=request.user
        )


        lecture = Lecture.objects.create(
            course=course,
            lecturer=request.user,
            title=title,
            audio_file=audio_file,
            status="pending"
        )

        make_audio_seekable(lecture.audio_file.path)
        # lecture.duration_seconds = (
        #     get_audio_duration(
        #         lecture.audio_file.path
        #     )
        # )

        # lecture.save(
        #     update_fields=[
        #         "duration_seconds"
        #     ]
        # )

        success, error = process_lecture_transcription(
            lecture
        )


        if success:

            messages.success(
                request,
                "Lecture uploaded and processed successfully."
            )

        else:

            messages.error(
                request,
                "Lecture was uploaded, but processing failed."
            )


        return redirect(
            "lecture_detail",
            lecture_id=lecture.id
        )