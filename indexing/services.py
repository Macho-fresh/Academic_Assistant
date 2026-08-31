from sklearn.feature_extraction.text import TfidfVectorizer

from lectures.models import TranscriptSegment, TopicSegment


def create_topic_label(text):

    if not text.strip():
        return "Lecture Topic"

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=3,
            ngram_range=(1, 2)
        )

        matrix = vectorizer.fit_transform([text])

        keywords = vectorizer.get_feature_names_out()

        if len(keywords) == 0:
            return "Lecture Topic"

        label = " ".join(
            word.title()
            for word in keywords[:3]
        )

        return label

    except ValueError:
        return "Lecture Topic"


def generate_topics(lecture):

    segments = list(
        TranscriptSegment.objects
        .filter(lecture=lecture)
        .order_by("start_seconds")
    )

    if not segments:
        return []

    # Remove topics generated during previous processing
    TopicSegment.objects.filter(
        lecture=lecture
    ).delete()

    topic_groups = []

    current_group = []
    current_start = None

    # Around 60 seconds per initial topic group.
    # We can make this smarter later.
    MAX_TOPIC_DURATION = 60

    for segment in segments:

        if current_start is None:
            current_start = segment.start_seconds

        current_group.append(segment)

        duration = (
            segment.end_seconds
            - current_start
        )

        if duration >= MAX_TOPIC_DURATION:

            topic_groups.append(
                current_group
            )

            current_group = []
            current_start = None

    # Add remaining transcript segments
    if current_group:
        topic_groups.append(
            current_group
        )

    topics = []

    for group in topic_groups:

        text = " ".join(
            segment.text
            for segment in group
        )

        topic_label = create_topic_label(
            text
        )

        topic = TopicSegment.objects.create(
            lecture=lecture,
            topic_label=topic_label,
            start_seconds=group[0].start_seconds,
            end_seconds=group[-1].end_seconds
        )

        topics.append(topic)

    return topics