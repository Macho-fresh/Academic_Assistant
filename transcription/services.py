from faster_whisper import WhisperModel


_model = None


def get_model():
    global _model

    if _model is None:
        print("Loading Whisper model...")

        _model = WhisperModel(
            "tiny",
            device="cpu",
            compute_type="int8"
        )

        print("Whisper model loaded successfully.")

    return _model


def transcribe_audio(audio_path):
    print("1. Starting transcription")
    model = get_model()

    print("2. Whisper model loaded")
    segments, info = model.transcribe(
        audio_path,
        beam_size=5
    )

    full_transcript = []
    timestamped_segments = []

    for segment in segments:
        print("4. Segment:", segment.text)
        text = segment.text.strip()

        full_transcript.append(text)

        timestamped_segments.append({
            "start": segment.start,
            "end": segment.end,
            "text": text
        })

    print("5. Transcription finished")
    return {
        "text": " ".join(full_transcript),
        "segments": timestamped_segments,
        "language": info.language
    }


import av
import os
import tempfile


def make_audio_seekable(audio_path):
    directory = os.path.dirname(audio_path)

    fd, temp_path = tempfile.mkstemp(
        suffix=".webm",
        dir=directory
    )
    os.close(fd)

    try:
        input_container = av.open(audio_path)
        output_container = av.open(
            temp_path,
            mode="w",
            format="webm"
        )

        input_stream = input_container.streams.audio[0]

        output_stream = output_container.add_stream(
            input_stream.codec_context.name,
            rate=input_stream.codec_context.sample_rate
        )

        for packet in input_container.demux(input_stream):
            for frame in packet.decode():
                for new_packet in output_stream.encode(frame):
                    output_container.mux(new_packet)

        # Flush encoder
        for packet in output_stream.encode():
            output_container.mux(packet)

        input_container.close()
        output_container.close()

        os.replace(temp_path, audio_path)

        return audio_path

    except Exception:
        if os.path.exists(temp_path):
            os.remove(temp_path)

        raise

import av


# def get_audio_duration(audio_path):

#     container = av.open(audio_path)

#     try:

#         if container.duration is not None:

#             duration_seconds = (
#                 container.duration
#                 / av.time_base
#             )

#             return float(
#                 duration_seconds
#             )

#         return 0

#     finally:

#         container.close()