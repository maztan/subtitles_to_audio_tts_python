from tts.tts_api_base import BaseTTS, tts_plugin
from winrt.windows.media.speechsynthesis import SpeechSynthesizer
from winrt.windows.storage.streams import DataReader, InputStreamOptions
import subprocess

@tts_plugin("winrt")
class WinRTTTS(BaseTTS):

    def __init__(self):
        self.client = SpeechSynthesizer()
        voice = self.pick_best_voice()
        print(f"Selected voice: {voice.display_name} ({voice.language})\n")
        self.client.voice = voice

    async def synthesize(self, text) -> bytes:
        stream = await self.client.synthesize_text_to_stream_async(text)

         # Get the underlying input stream
        input_stream = stream.get_input_stream_at(0)

        reader = DataReader(input_stream)
        reader.input_stream_options = InputStreamOptions.READ_AHEAD

        size = stream.size
        await reader.load_async(size)

        data = reader.read_buffer(size) #read_bytes(stream) , this could reuse the buffer (good idea?)

        reader.close()
        stream.close()

        return bytes(data)

    def wav_to_mp3(self, wav_data: bytes) -> bytes:
        p = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-i", "pipe:0",
                "-f", "mp3",
                "pipe:1"
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        out, err = p.communicate(wav_data)

        if p.returncode != 0:
            raise RuntimeError(err.decode(errors="ignore"))

        return out
    
    def pick_best_voice(self, language_prefix : str ="en"):
        voices = SpeechSynthesizer.all_voices

        # 1. Filter by language
        candidates = [
            v for v in voices
            if v.language.lower().startswith(language_prefix.lower())
        ]

        for v in candidates:
            print(v.display_name, str(v.language), v.gender)

        # 2. Prefer high-quality / neural voices if available
        preferred_keywords = ["neural", "online", "natural"]

        for keyword in preferred_keywords:
            for v in candidates:
                if keyword in v.display_name.lower():
                    return v

        # 3. Fallback: first matching language voice
        if candidates:
            return candidates[0]

        # 4. Final fallback: system default
        return SpeechSynthesizer.default_voice
        