import io
from os import PathLike
from typing import BinaryIO, Tuple

import numpy as np
import soundfile as sf
import python_stretch as ps

class AudioHelper:
    @staticmethod
    def shorten_to_duration(input_path: BinaryIO | str | PathLike, output_path, target_duration):
        audio, sr = sf.read(input_path)

        source_duration = audio.shape[0] # in frames
        target_duration = int(target_duration * sr)
        #ratio = source_duration / target_duration
        ratio = target_duration / source_duration

        if ratio >= 1.0:
            print(f"Audio is shorter than target duration, no need to shorten. Source duration: {source_duration/sr:.2f} sec, target duration: {target_duration/sr:.2f} sec")
            return False

        audio =np.asarray(audio, dtype=np.float32)
        audio = audio[:, None] if audio.ndim == 1 else audio
        
        # Assure that "audio" is a 2d array
        # if (audio.ndim == 1):
        #     audio = audio[np.newaxis, :]

        # Create a Stretch object
        stretch = ps.Signalsmith.Stretch()
        # Configure using a preset
        num_channels = audio.shape[1] if audio.ndim > 1 else 1
        stretch.preset(num_channels, sr) # numChannels, sampleRate
        # Shift up by one octave
        #stretch.setTransposeSemitones(12)
        # Stretch time
        stretch.timeFactor = ratio
        
        print(f"Shortening audio from {source_duration/sr:.2f} sec to {target_duration/sr:.2f} sec (ratio: {ratio:.2f})")

        # Process
        audio_processed = stretch.process(audio)
       
        sf.write(output_path, np.squeeze(audio_processed), sr, format="WAV") #TODO: format should be the same as input not "WAV"
        #sf.write(output_path, y_stretched, sr)
        #sf.write(output_path, y_stretched, sr, format="WAV") #TODO: format should be the same as input not "WAV"

        return True
    
    def shorten_to_duration(
        audio_input: BinaryIO,
        target_seconds: float,
        output_format: str = "WAV",
    ) -> Tuple[BinaryIO, bool]:
        """
        Speed up (or slow down) audio in a BinaryIO to match a target duration.

        Args:
            audio_input:     Any file-like object containing audio (WAV, FLAC, OGG, …).
            target_seconds:  Desired output duration in seconds.
            output_format:   Output container format passed to soundfile (default: "WAV").

        Returns:
            A tuple containing the re-timed audio at the original sample rate and a boolean indicating whether the audio was actually stretched.
            If the input audio already matched the target duration (within a small tolerance), the original audio is returned without modification and the boolean is False.

        Raises:
            ValueError: If target_seconds is non-positive.
        """
        if target_seconds <= 0:
            raise ValueError(f"target_seconds must be > 0, got {target_seconds}")

        # --- 1. Decode input -------------------------------------------------
        audio_input.seek(0)
        audio, sr = sf.read(audio_input, dtype="float32", always_2d=True)
        # audio shape: (num_samples, num_channels)  — soundfile is channels-last

        original_seconds = audio.shape[0] / sr
        time_factor = original_seconds / target_seconds  # >1 = speed up, <1 = slow down

        if abs(time_factor - 1.0) < 1e-6:          # already the right length
            audio_input.seek(0)
            return audio_input, False

        # --- 2. Transpose to (channels, samples) expected by python-stretch --
        audio_c_first = audio.T.copy()              # shape: (channels, samples)
        num_channels = audio_c_first.shape[0]

        # --- 3. Configure Signalsmith Stretch --------------------------------
        stretcher = ps.Signalsmith.Stretch()
        stretcher.preset(num_channels, sr)
        stretcher.timeFactor = time_factor          # >1 compresses time (speeds up)

        # --- 4. Process ------------------------------------------------------
        stretched = stretcher.process(audio_c_first)   # returns (channels, new_samples)

        # --- 5. Encode to output BinaryIO ------------------------------------
        output = io.BytesIO()
        sf.write(output, stretched.T, sr, format=output_format)
        output.seek(0)
        return output, True

    @staticmethod
    def get_duration(input_path: BinaryIO | str | PathLike):
        # not the fastest; maybe switch to header decoding for formats that support it (like wav)
        info = sf.info(input_path)
        return info.frames / info.samplerate