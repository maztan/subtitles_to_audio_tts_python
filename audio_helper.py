import io
from os import PathLike
from typing import BinaryIO, Tuple

import numpy as np
import soundfile as sf
import python_stretch

class AudioHelper:
    @staticmethod
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
        stretcher = python_stretch.Signalsmith.Stretch()
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