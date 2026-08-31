from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from lectures.models import LectureSummary


_tokenizer = None
_model = None


def get_summary_model():
    global _tokenizer, _model

    if _tokenizer is None or _model is None:

        print("Loading summary model...")

        model_name = "google/flan-t5-small"

        _tokenizer = AutoTokenizer.from_pretrained(
            model_name
        )

        _model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name
        )

        print("Summary model loaded.")

    return _tokenizer, _model


def chunk_text(text, max_words=300):

    words = text.split()

    return [
        " ".join(words[i:i + max_words])
        for i in range(
            0,
            len(words),
            max_words
        )
    ]

def run_model(prompt, max_new_tokens=120):

    tokenizer, model = get_summary_model()

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=512
    )

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        num_beams=5,
        repetition_penalty=1.2,
        no_repeat_ngram_size=2,
        early_stopping=True
    )

    return tokenizer.decode(
        outputs[0],
        skip_special_tokens=True
    ).strip()

def generate_summary(text):

    if not text or not text.strip():
        return {
            "summary": "",
            "key_points": []
        }

    chunks = chunk_text(text)

    chunk_summaries = []

    for chunk in chunks:

        prompt = (
            "Summarize this lecture in your own words: "
            + chunk
        )

        summary = run_model(
            prompt,
            max_new_tokens=100
        )

        if summary:
            chunk_summaries.append(summary)

    combined_summary = " ".join(
        chunk_summaries
    ).strip()

    key_points = generate_key_points(
        text
    )

    return {
        "summary": combined_summary,
        "key_points": key_points
    }


def generate_key_points(text):

    if not text or not text.strip():
        return []

    prompt = (
        "List the important ideas from this lecture. "
        "One idea per line: "
        + text
    )

    result = run_model(
        prompt,
        max_new_tokens=120
    )

    lines = [
        line.strip()
        for line in result.split("\n")
        if line.strip()
    ]

    cleaned_points = []

    for line in lines:

        line = line.lstrip(
            "-•0123456789. )"
        ).strip()

        if line:
            cleaned_points.append(line)

    return cleaned_points[:5]

def save_lecture_summary(lecture):

    result = generate_summary(
        lecture.transcript
    )

    print(
        "GENERATED SUMMARY:",
        result["summary"]
    )

    print(
        "GENERATED KEY POINTS:",
        result["key_points"]
    )

    summary, created = (
        LectureSummary.objects.update_or_create(
            lecture=lecture,
            defaults={
                "summary_text": result["summary"],
                "key_points": result["key_points"],
            }
        )
    )

    return summary