# from unittest.mock import patch, MagicMock


# class TranscriptionServiceAPITestCase(APITestCase):

#     @patch(
#         "transcription.services.get_model"
#     )
#     def test_transcription_returns_text_and_segments(
#         self,
#         mock_get_model
#     ):

#         segment = MagicMock()

#         segment.start = 0.0
#         segment.end = 5.2
#         segment.text = "Introduction to compiler design."

#         info = MagicMock()
#         info.language = "en"

#         model = MagicMock()

#         model.transcribe.return_value = (
#             [segment],
#             info
#         )

#         mock_get_model.return_value = model

#         from transcription.services import transcribe_audio

#         result = transcribe_audio(
#             "fake_audio.webm"
#         )

#         self.assertEqual(
#             result["text"],
#             "Introduction to compiler design."
#         )

#         self.assertEqual(
#             result["language"],
#             "en"
#         )

#         self.assertEqual(
#             len(result["segments"]),
#             1
#         )

#         self.assertEqual(
#             result["segments"][0]["start"],
#             0.0
#         )