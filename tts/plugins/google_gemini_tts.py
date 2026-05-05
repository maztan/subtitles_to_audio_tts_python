from dataclasses import dataclass
from io import BytesIO
import os
import wave

from google import genai
from tts.tts_api_base import BaseTTS, tts_plugin

@tts_plugin("gemini")
class GoogleGeminiTTS(BaseTTS):

    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GOOGLE_GEMINI_API_KEY"))

    async def synthesize(self, text) -> bytes:
        response = self.client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config={
                "response_modalities": ["AUDIO"]
            }
        )

        #Sometimes gives: part = response.candidates[0].content.parts[0]
                                #~~~~~~~~~~~~~~~~~~~^^^
                                # TypeError: 'NoneType' object is not subscriptable
        # Extract audio bytes
        part = response.candidates[0].content.parts[0]

        audio_bytes = part.inline_data.data        # <- raw bytes
        mime_type = part.inline_data.mime_type    # e.g. 'audio/wav' or "audio/L16;codec=pcm;rate=24000"

        mime_info = self.parse_mime_type(mime_type)
        
        buff = BytesIO()
        self.pcm_to_wav(audio_bytes, mime_info, buff)
        return buff.getvalue()

    def list_models(self):
        models = self.client.models.list()
        for model in models:
            # some SDK versions use different field names, so be defensive
            modalities = getattr(model, "supported_generation_modalities", None) \
                    or getattr(model, "generation_modalities", None) \
                    or []
            
            print(f"{model.name} \t supports audio?: {"yes" if "AUDIO" in modalities else "no"}")
            print(modalities)

    def parse_mime_type(self, mime: str) -> AudioMimeInfo:
        """Parses e.g. "audio/L16;codec=pcm;rate=24000"
        """

        # Parse base type (L16, L8, etc.)
        base = mime.split(";")[0].split("/")[1]
        pcm_bits = int(base[1:]) if base.startswith("L") and base[1:].isdigit() else None

        type = base[0]
        subtype = base[1:]
        pcm_sampwidth = pcm_bits // 8 if pcm_bits is not None else None

        # Parse params
        params = {}
        for item in mime.split(";")[1:]:
            k, v = item.split("=")
            params[k.strip()] = v.strip()

        rate = int(params.get("rate", None))

        val = params.get("channels")
        channels = int(val) if val is not None else None

        encoding = "unknown"
        if params.get("codec") is not None or type.startswith("L"):
            encoding = "pcm"

        return AudioMimeInfo(
            original_mime_str=mime,
            type=type,
            subtype=subtype,
            encoding=encoding,
            rate=rate,
            channels=channels,
            pcm_bits=pcm_bits,
            pcm_sampwidth=pcm_sampwidth,
            all_params=params
        )

    
    def pcm_to_wav(self, audio_bytes: bytes, mime_type: AudioMimeInfo, output: str | BytesIO):

        if mime_type.encoding != "pcm":
            raise ValueError(f"Mime type encoding is not PCM: {mime_type.encoding}")
                
        with wave.open(output, "wb") as f:
            f.setnchannels(mime_type.channels if mime_type.channels is not None else 1)
            f.setsampwidth(mime_type.pcm_sampwidth)
            f.setframerate(mime_type.rate if mime_type.rate is not None else 24000)
            f.writeframes(audio_bytes)


@dataclass
class AudioMimeInfo:
    original_mime_str: str
    type: str
    subtype: str
    encoding: str
    pcm_bits: int | None
    pcm_sampwidth: int | None
    rate: int | None
    channels: int | None
    all_params: dict

            