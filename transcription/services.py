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

    directory = os.path.dirname(
        audio_path
    )

    base_name = os.path.splitext(
        os.path.basename(audio_path)
    )[0]

    extension = os.path.splitext(
        audio_path
    )[1].lower()


    # Don't overwrite an existing M4A
    if extension == ".m4a":

        new_path = os.path.join(
            directory,
            f"{base_name}_seekable.m4a"
        )

    else:

        new_path = os.path.join(
            directory,
            f"{base_name}.m4a"
        )


    input_container = None
    output_container = None

    try:

        print(
            "Opening audio:",
            audio_path
        )


        input_container = av.open(
            audio_path
        )


        if not input_container.streams.audio:

            raise ValueError(
                "The file does not contain an audio stream."
            )


        input_stream = (
            input_container.streams.audio[0]
        )


        print(
            "Input codec:",
            input_stream.codec_context.name
        )

        print(
            "Input sample rate:",
            input_stream.codec_context.sample_rate
        )

        print(
            "Input layout:",
            input_stream.codec_context.layout
        )


        output_container = av.open(
            new_path,
            mode="w",
            format="mp4"
        )


        output_stream = (
            output_container.add_stream(
                "aac",
                rate=44100
            )
        )

        output_stream.layout = "mono"


        # Convert all incoming audio to a consistent
        # format before sending it to the AAC encoder.
        resampler = av.AudioResampler(
            format="fltp",
            layout="mono",
            rate=44100
        )


        for frame in input_container.decode(
            audio=0
        ):

            resampled_frames = (
                resampler.resample(
                    frame
                )
            )


            for resampled_frame in resampled_frames:

                resampled_frame.pts = None


                for packet in output_stream.encode(
                    resampled_frame
                ):

                    output_container.mux(
                        packet
                    )


        # Flush remaining resampled audio
        remaining_frames = (
            resampler.resample(None)
        )


        for frame in remaining_frames:

            frame.pts = None


            for packet in output_stream.encode(
                frame
            ):

                output_container.mux(
                    packet
                )


        # Flush AAC encoder
        for packet in output_stream.encode(
            None
        ):

            output_container.mux(
                packet
            )


        input_container.close()
        input_container = None


        output_container.close()
        output_container = None


        print(
            "Seekable audio created:",
            new_path
        )


        return new_path


    except Exception as error:

        print(
            "Audio conversion error:",
            error
        )


        if input_container is not None:
            input_container.close()


        if output_container is not None:
            output_container.close()


        if (
            os.path.exists(new_path)
            and new_path != audio_path
        ):
            os.remove(
                new_path
            )


        raise


def get_audio_duration(audio_path):

    container = av.open(audio_path)

    try:

        if container.duration is not None:

            duration_seconds = (
                container.duration
                / av.time_base
            )

            return float(
                duration_seconds
            )

        return 0

    finally:

        container.close()