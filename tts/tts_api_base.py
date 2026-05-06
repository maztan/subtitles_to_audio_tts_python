# def test_tts():
#     client = SAPIClient()
#     client.speak("Hello, this is a test of the text to speech API.")

from abc import ABC, abstractmethod
import inspect

# Global plugin registry
TTS_REGISTRY = {}

def tts_plugin(name: str):
    """
    Class decorator to register a TTS engine plugin.
    """
    def decorator(cls):
        if inspect.isabstract(cls):
            raise TypeError("Cannot register abstract class")
        
        # enforce correct base class
        if not issubclass(cls, BaseTTS):
            raise TypeError(
                f"@tts_plugin '{name}' can only be used on BaseTTS subclasses. "
                f"Got: {cls.__name__}"
            )
        
        if name in TTS_REGISTRY:
            raise KeyError(f"Duplicate plugin: {name}")
        
        TTS_REGISTRY[name] = cls
        cls.plugin_name = name
        return cls
    return decorator

def get_tts_engine(name: str, **kwargs) -> BaseTTS:
    """Factory function to lookup and return an instance of a registered TTS engine by name."""
    if name not in TTS_REGISTRY:
        raise ValueError(f"TTS engine '{name}' not found")

    engine_cls = TTS_REGISTRY[name]
    return engine_cls(**kwargs)

class BaseTTS(ABC):
    """Abstract base class for text-to-speech engines."""

    @abstractmethod
    async def synthesize(self, text: str) -> tuple[bytes, str]:
        """
        Convert text to speech.

        Returns:
            A tuple containing the audio data as bytes and the audio format (e.g., "WAV", "MP3").
        """
        pass


