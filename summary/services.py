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


def chunk_text(text, max_words=220):
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

        min_new_tokens=30,

        num_beams=6,

        length_penalty=1.5,

        repetition_penalty=1.3,

        no_repeat_ngram_size=3,

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
            "Summarize the following lecture transcript "
            "in 2 to 4 clear sentences. "
            "Only describe what is said in the transcript. "
            "Do not ask questions. "
            "Do not repeat the instruction.\n\n"
            f"Transcript:\n{chunk}\n\n"
            "Summary:"
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

    # If there were several chunks,
    # summarize the summaries again.
    if len(chunk_summaries) > 1:

        final_prompt = (
            "Combine the following lecture summaries "
            "into one concise academic summary. "
            "Use 3 to 5 sentences. "
            "Do not add information that is not present.\n\n"
            f"{combined_summary}\n\n"
            "Final summary:"
        )

        combined_summary = run_model(
            final_prompt,
            max_new_tokens=140
        )

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

    text = " ".join(
        text.split()[:300]
    )

    key_points = []

    prompts = [
        (
            "What is the main idea discussed in this "
            "lecture transcript? Answer with one factual "
            "sentence based only on the transcript.\n\n"
            f"Transcript:\n{text}\n\n"
            "Main idea:"
        ),

        (
            "What is one important supporting fact from "
            "this lecture transcript? Answer with one "
            "short factual sentence.\n\n"
            f"Transcript:\n{text}\n\n"
            "Important fact:"
        ),

        (
            "What conclusion or question does the speaker "
            "raise in this lecture transcript? Answer with "
            "one short sentence based only on the transcript.\n\n"
            f"Transcript:\n{text}\n\n"
            "Point:"
        )
    ]

    for prompt in prompts:

        point = run_model(
            prompt,
            max_new_tokens=60
        )

        point = point.strip()

        if (
            point
            and point not in key_points
        ):
            key_points.append(point)

    return key_points[:5]

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