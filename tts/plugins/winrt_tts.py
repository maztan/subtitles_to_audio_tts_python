from tts.tts_api_base import BaseTTS, tts_plugin
from winrt.windows.media.speechsynthesis import SpeechSynthesizer
from winrt.windows.storage.streams import DataReader, InputStreamOptions
from pydub import AudioSegment
import io

@tts_plugin("winrt")
class WinRTTTS(BaseTTS):

    def __init__(self):
        self.client = SpeechSynthesizer()

    async def synthesize(self, text):
        stream = await self.client.synthesize_text_to_stream_async(text)

         # Get the underlying input stream
        input_stream = stream.get_input_stream_at(0)

        reader = DataReader(input_stream)
        reader.input_stream_options = InputStreamOptions.READ_AHEAD

        size = stream.size
        await reader.load_async(size)

        data = reader.read_bytes(size)

        reader.close()
        stream.close()

        return bytes(data)

    def wav_to_mp3(self, wav_data: bytes) -> bytes:
        # Wrap bytes as file-like object
        # pydub auto-detects WAV from header
        audio = AudioSegment.from_file(io.BytesIO(wav_data), format="wav")
        mp3_io = io.BytesIO()
        audio.export(mp3_io, format="mp3")
        return mp3_io.getvalue()
        