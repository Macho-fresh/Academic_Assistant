import re

from lectures.models import Lecture
from timetable.models import Timetable
from django.utils import timezone
from datetime import timedelta


STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "what",
    "where",
    "when",
    "how",
    "why",
    "who",
    "did",
    "does",
    "do",
    "about",
    "in",
    "on",
    "to",
    "of",
    "for",
    "my",
    "me",
    "please",
    "can",
    "could",
    "would",
    "tell",
    "show",
    "find",
    "lecture",
    "lecturer",
    "said",
    "say",
    "explain",
    "explained",
    "discuss",
    "discussed",
}


def extract_keywords(query):
    """
    Convert the user's question into useful search keywords.
    """

    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        query.lower()
    )

    keywords = []

    for word in words:

        if (
            word not in STOP_WORDS
            and len(word) > 2
        ):
            keywords.append(word)

    return keywords


def calculate_score(text, keywords):
    """
    Calculate how well a piece of text matches the question.
    """

    if not text:
        return 0

    text = text.lower()

    score = 0

    for keyword in keywords:

        if keyword in text:
            score += 1

        # Give slightly more weight
        # when the word appears multiple times
        score += min(
            text.count(keyword),
            3
        ) * 0.25

    return score


def format_timestamp(seconds):
    """
    Convert seconds into MM:SS or HH:MM:SS.
    """

    if seconds is None:
        return None

    seconds = int(seconds)

    hours = seconds // 3600

    minutes = (
        seconds % 3600
    ) // 60

    remaining_seconds = (
        seconds % 60
    )

    if hours > 0:

        return (
            f"{hours:02}:"
            f"{minutes:02}:"
            f"{remaining_seconds:02}"
        )

    return (
        f"{minutes:02}:"
        f"{remaining_seconds:02}"
    )


def get_user_lectures(user):
    """
    Return the lectures that the current user
    is allowed to search.
    """

    lectures = Lecture.objects.filter(
        status="completed"
    ).select_related(
        "course",
        "lecturer"
    )

    if user.role == "lecturer":

        lectures = lectures.filter(
            lecturer=user
        )

    return lectures


def get_transcript_segments(lecture):
    """
    Safely retrieve timestamped transcript segments.

    Adjust the related-name checks here if your
    transcript segment model uses a different name.
    """

    possible_related_names = [
        "transcript_segments",
        "segments",
        "transcriptsegment_set",
    ]

    for related_name in possible_related_names:

        if hasattr(
            lecture,
            related_name
        ):

            manager = getattr(
                lecture,
                related_name
            )

            try:
                return list(
                    manager.all()
                )

            except Exception:
                pass

    return []


def get_topic_segments(lecture):
    """
    Safely retrieve topic segments.

    Adjust the related-name checks if needed.
    """

    possible_related_names = [
        "topic_segments",
        "topics",
        "topicsegment_set",
    ]

    for related_name in possible_related_names:

        if hasattr(
            lecture,
            related_name
        ):

            manager = getattr(
                lecture,
                related_name
            )

            try:
                return list(
                    manager.all()
                )

            except Exception:
                pass

    return []


def get_lecture_summary(lecture):
    """
    Safely retrieve the summary associated
    with a lecture.
    """

    possible_related_names = [
        "summary",
        "lecture_summary",
        "lecturesummary",
    ]

    for related_name in possible_related_names:

        if hasattr(
            lecture,
            related_name
        ):

            try:
                return getattr(
                    lecture,
                    related_name
                )

            except Exception:
                pass

    return None


def get_segment_text(segment):
    """
    Safely retrieve transcript segment text.
    """

    possible_fields = [
        "text",
        "content",
        "transcript",
    ]

    for field in possible_fields:

        if hasattr(
            segment,
            field
        ):

            value = getattr(
                segment,
                field
            )

            if value:
                return str(value)

    return ""


def get_segment_start(segment):
    """
    Safely retrieve a transcript segment's
    starting timestamp.
    """

    possible_fields = [
        "start",
        "start_time",
        "start_seconds",
        "start_timestamp",
    ]

    for field in possible_fields:

        if hasattr(
            segment,
            field
        ):

            value = getattr(
                segment,
                field
            )

            if value is not None:

                try:
                    return float(value)

                except (
                    TypeError,
                    ValueError
                ):
                    pass

    return None


def get_topic_text(topic):
    """
    Safely retrieve the topic title/name.
    """

    possible_fields = [
        "title",
        "topic",
        "topic_name",
        "label",
        "name",
    ]

    for field in possible_fields:

        if hasattr(
            topic,
            field
        ):

            value = getattr(
                topic,
                field
            )

            if value:
                return str(value)

    return ""


def get_topic_start(topic):
    """
    Safely retrieve topic starting timestamp.
    """

    possible_fields = [
        "start",
        "start_time",
        "start_seconds",
        "timestamp",
    ]

    for field in possible_fields:

        if hasattr(
            topic,
            field
        ):

            value = getattr(
                topic,
                field
            )

            if value is not None:

                try:
                    return float(value)

                except (
                    TypeError,
                    ValueError
                ):
                    pass

    return None


def get_summary_text(summary):
    """
    Get the summary text regardless of the exact field name.
    """

    if summary is None:
        return ""

    possible_fields = [
        "summary_text",
        "summary",
        "text",
    ]

    for field in possible_fields:

        if hasattr(
            summary,
            field
        ):

            value = getattr(
                summary,
                field
            )

            if value:
                return str(value)

    return ""


def get_key_points(summary):
    """
    Retrieve key points if they exist.
    """

    if summary is None:
        return []

    if hasattr(
        summary,
        "key_points"
    ):

        points = summary.key_points

        if isinstance(
            points,
            list
        ):
            return points

        if isinstance(
            points,
            str
        ):

            return [
                line.strip()
                for line in points.splitlines()
                if line.strip()
            ]

    return []


def find_best_match(user, query):
    """
    Search all accessible lectures and return
    the most relevant result.
    """

    keywords = extract_keywords(
        query
    )

    if not keywords:

        return None

    lectures = get_user_lectures(
        user
    )

    best_result = None
    best_score = 0

    for lecture in lectures:

        # =====================================
        # LECTURE TITLE
        # =====================================

        title_score = (
            calculate_score(
                lecture.title,
                keywords
            )
            * 2
        )

        if title_score > best_score:

            best_score = title_score

            best_result = {
                "type": "lecture",
                "lecture": lecture,
                "score": title_score,
                "text": lecture.title,
                "timestamp": None,
            }

        # =====================================
        # COURSE
        # =====================================

        course_text = (
            f"{lecture.course.course_code} "
            f"{lecture.course.course_title}"
        )

        course_score = (
            calculate_score(
                course_text,
                keywords
            )
            * 1.5
        )

        if course_score > best_score:

            best_score = course_score

            best_result = {
                "type": "course",
                "lecture": lecture,
                "score": course_score,
                "text": course_text,
                "timestamp": None,
            }

        # =====================================
        # FULL TRANSCRIPT
        # =====================================

        transcript_score = calculate_score(
            lecture.transcript or "",
            keywords
        )

        if transcript_score > best_score:

            best_score = transcript_score

            best_result = {
                "type": "transcript",
                "lecture": lecture,
                "score": transcript_score,
                "text": lecture.transcript,
                "timestamp": None,
            }

        # =====================================
        # TRANSCRIPT SEGMENTS
        # =====================================

        segments = get_transcript_segments(
            lecture
        )

        for segment in segments:

            segment_text = get_segment_text(
                segment
            )

            segment_score = (
                calculate_score(
                    segment_text,
                    keywords
                )
                * 3
            )

            if segment_score > best_score:

                best_score = segment_score

                best_result = {
                    "type": "segment",
                    "lecture": lecture,
                    "score": segment_score,
                    "text": segment_text,
                    "timestamp": get_segment_start(
                        segment
                    ),
                }

        # =====================================
        # TOPICS
        # =====================================

        topics = get_topic_segments(
            lecture
        )

        for topic in topics:

            topic_text = get_topic_text(
                topic
            )

            topic_score = (
                calculate_score(
                    topic_text,
                    keywords
                )
                * 3
            )

            if topic_score > best_score:

                best_score = topic_score

                best_result = {
                    "type": "topic",
                    "lecture": lecture,
                    "score": topic_score,
                    "text": topic_text,
                    "timestamp": get_topic_start(
                        topic
                    ),
                }

        # =====================================
        # SUMMARY
        # =====================================

        summary = get_lecture_summary(
            lecture
        )

        summary_text = get_summary_text(
            summary
        )

        summary_score = (
            calculate_score(
                summary_text,
                keywords
            )
            * 2
        )

        if summary_score > best_score:

            best_score = summary_score

            best_result = {
                "type": "summary",
                "lecture": lecture,
                "score": summary_score,
                "text": summary_text,
                "timestamp": None,
            }

        # =====================================
        # KEY POINTS
        # =====================================

        key_points = get_key_points(
            summary
        )

        for point in key_points:

            point_score = (
                calculate_score(
                    point,
                    keywords
                )
                * 2
            )

            if point_score > best_score:

                best_score = point_score

                best_result = {
                    "type": "key_point",
                    "lecture": lecture,
                    "score": point_score,
                    "text": point,
                    "timestamp": None,
                }

    return best_result

def is_timetable_question(query):
    query = query.lower()

    timetable_phrases = [
        "timetable",
        "schedule",
        "next class",
        "classes today",
        "class today",
        "classes tomorrow",
        "class tomorrow",
        "what class",
        "what classes",
        "when is",
        "where is my class",
        "where is my next class",
    ]

    days = [
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    ]

    return (
        any(
            phrase in query
            for phrase in timetable_phrases
        )
        or (
            "class" in query
            and any(day in query for day in days)
        )
    )

def answer_timetable_question(user, query):

    query = query.lower()

    entries = (
        Timetable.objects
        .filter(owner=user)
        .select_related("course")
        .order_by("start_time")
    )

    if not entries.exists():
        return {
            "answer": "You don't have any classes in your timetable yet.",
            "lecture": None,
            "course": None,
            "course_title": None,
            "lecture_id": None,
            "timestamp": None,
            "timestamp_display": None,
            "match_type": "timetable",
            "score": 1,
        }

    today = timezone.localdate()

    day_names = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    # ------------------------------
    # DETERMINE REQUESTED DAY
    # ------------------------------

    requested_day = None

    if "today" in query:

        requested_day = today.strftime("%A")

    elif "tomorrow" in query:

        tomorrow = today + timedelta(days=1)

        requested_day = tomorrow.strftime("%A")

    else:

        for day in day_names:

            if day.lower() in query:

                requested_day = day
                break


    # ------------------------------
    # SPECIFIC COURSE
    # ------------------------------

    for entry in entries:

        course_code = entry.course.course_code.lower()

        course_title = entry.course.course_title.lower()

        if (
            course_code in query
            or course_title in query
        ):

            answer = (
                f"{entry.course.course_code} - "
                f"{entry.course.course_title} is scheduled "
                f"on {entry.day} from "
                f"{entry.start_time.strftime('%I:%M %p')} to "
                f"{entry.end_time.strftime('%I:%M %p')}"
            )

            if entry.venue:

                answer += (
                    f" at {entry.venue}"
                )

            answer += "."

            return {
                "answer": answer,
                "lecture": None,
                "course": entry.course.course_code,
                "course_title": entry.course.course_title,
                "lecture_id": None,
                "timestamp": None,
                "timestamp_display": None,
                "match_type": "timetable",
                "score": 1,
            }


    # ------------------------------
    # SPECIFIC DAY
    # ------------------------------

    if requested_day:

        day_entries = entries.filter(
            day__iexact=requested_day
        )

        if not day_entries.exists():

            answer = (
                f"You don't have any classes "
                f"scheduled for {requested_day}."
            )

        else:

            lines = []

            for entry in day_entries:

                class_text = (
                    f"{entry.course.course_code} - "
                    f"{entry.course.course_title}, "
                    f"{entry.start_time.strftime('%I:%M %p')} - "
                    f"{entry.end_time.strftime('%I:%M %p')}"
                )

                if entry.venue:

                    class_text += (
                        f", {entry.venue}"
                    )

                lines.append(class_text)

            answer = (
                f"Your classes for {requested_day} are:\n"
                + "\n".join(lines)
            )

        return {
            "answer": answer,
            "lecture": None,
            "course": None,
            "course_title": None,
            "lecture_id": None,
            "timestamp": None,
            "timestamp_display": None,
            "match_type": "timetable",
            "score": 1,
        }


    # ------------------------------
    # COMPLETE TIMETABLE
    # ------------------------------

    lines = []

    for day in day_names:

        day_entries = entries.filter(
            day__iexact=day
        )

        for entry in day_entries:

            class_text = (
                f"{day}: "
                f"{entry.course.course_code} - "
                f"{entry.course.course_title}, "
                f"{entry.start_time.strftime('%I:%M %p')} - "
                f"{entry.end_time.strftime('%I:%M %p')}"
            )

            if entry.venue:

                class_text += (
                    f", {entry.venue}"
                )

            lines.append(class_text)

    return {
        "answer": (
            "Here is your timetable:\n"
            + "\n".join(lines)
        ),
        "lecture": None,
        "course": None,
        "course_title": None,
        "lecture_id": None,
        "timestamp": None,
        "timestamp_display": None,
        "match_type": "timetable",
        "score": 1,
    }

def answer_question(user, query):
    """
    Main function used by the assistant view.
    """

    query = query.strip()

    if not query:

        return {
            "answer": "Please enter a question.",
            "lecture": None,
            "course": None,
            "lecture_id": None,
            "timestamp": None,
            "timestamp_display": None,
        }

    if is_timetable_question(query):

        return answer_timetable_question(
            user,
            query
        )

    result = find_best_match(
        user,
        query
    )

    if (
        not result
        or result["score"] <= 0
    ):

        return {
            "answer": (
                "I couldn't find anything related to "
                "that question in your processed lectures."
            ),
            "lecture": None,
            "course": None,
            "lecture_id": None,
            "timestamp": None,
            "timestamp_display": None,
        }

    lecture = result[
        "lecture"
    ]

    result_type = result[
        "type"
    ]

    result_text = result[
        "text"
    ]

    timestamp = result[
        "timestamp"
    ]

    # =====================================
    # BUILD RESPONSE
    # =====================================

    if result_type == "segment":

        answer = result_text

    elif result_type == "topic":

        answer = (
            f"This topic was discussed in "
            f"'{lecture.title}'. "
            f"The indexed topic is: "
            f"{result_text}."
        )

    elif result_type == "summary":

        answer = result_text

    elif result_type == "key_point":

        answer = result_text

    elif result_type == "transcript":

        # Avoid returning a massive transcript
        answer = result_text[:600]

        if len(
            result_text
        ) > 600:

            answer += "..."

    elif result_type == "lecture":

        summary = get_lecture_summary(
            lecture
        )

        summary_text = get_summary_text(
            summary
        )

        if summary_text:

            answer = summary_text

        else:

            answer = (
                f"I found the lecture "
                f"'{lecture.title}'."
            )

    elif result_type == "course":

        answer = (
            f"I found a relevant lecture "
            f"in {lecture.course.course_code} - "
            f"{lecture.course.course_title}: "
            f"{lecture.title}."
        )

    else:

        answer = result_text

    return {
        "answer": answer,

        "lecture": lecture.title,

        "course": (
            lecture.course.course_code
        ),

        "course_title": (
            lecture.course.course_title
        ),

        "lecture_id": lecture.id,

        "timestamp": timestamp,

        "timestamp_display": format_timestamp(
            timestamp
        ),

        "match_type": result_type,

        "score": round(
            result["score"],
            2
        ),
    }