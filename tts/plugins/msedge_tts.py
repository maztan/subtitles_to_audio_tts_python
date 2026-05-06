from email.mime import text
import io

from tts.tts_api_base import BaseTTS, tts_plugin
import edge_tts

VOICE = "en-US-AndrewNeural"
OUTPUT_FILE = "test.mp3"

@tts_plugin("msedge")
class MSEdgeTTS(BaseTTS):

    def __init__(self):
        pass

    async def synthesize(self, text) -> tuple[bytes, str]:
        audio_bytes = io.BytesIO()
        communicate = edge_tts.Communicate(text, voice=VOICE)
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes.write(chunk["data"])
        audio_bytes.seek(0)
        return audio_bytes.getvalue(), "MP3"

    async def list_voices(self):
        voices = await edge_tts.list_voices()
        for v in voices:
            print(v["ShortName"], v["Locale"], v["Gender"])