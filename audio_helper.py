import io
import math
from os import PathLike
import subprocess
from typing import BinaryIO, Iterable, Tuple
import wave

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
        audio_c_first = audio.T.copy()            # shape: (channels, samples)
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
    
    def join_wavs_to_mp3(
        wav_paths: list[str],
        wav_pauses_sec_between: list[float] | None,
        output_mp3: str,
        silence_seconds: float,
        bitrate: int = 128,
        chunk_frames: int = 4096,
    ) -> None:
        """
        Join WAV files into a single MP3, inserting silence between each file.
        Audio is streamed — no full file is loaded into memory at once.
        MP3 frames are written to disk on the fly via an ffmpeg pipe.

        Args:
            wav_paths:       Ordered iterable of paths to .wav files.
            wav_pauses_sec_between: Iterable of seconds of silence to insert between each consecutive pair of WAV files.
                              Must have length one less than wav_paths (i.e. no pause after the last file).
                              If None, no silence will be inserted between files.
            output_mp3:      Destination .mp3 file path.
            silence_seconds: Seconds of silence to insert between consecutive files
                            (can be fractional, e.g. 0.5 or 2.75).
            bitrate:         MP3 bitrate in kbps (default: 128).
            chunk_frames:    PCM frames read per iteration (controls RAM usage).

        Raises:
            ValueError:  If WAV files have mismatched sample rates or channel counts.
            RuntimeError: If ffmpeg is not available or exits with an error.
        """

        paths = wav_paths
        if not paths:
            raise ValueError("wav_paths is empty")
        
        if wav_pauses_sec_between is not None and len(wav_pauses_sec_between) != len(paths) - 1:
            raise ValueError(
                f"wav_pauses_sec_between must have length one less than wav_paths, "
                f"got {len(wav_pauses_sec_between)} pauses for {len(paths)} files"
            )

        # --- Probe the first file to get stream parameters -------------------
        with wave.open(paths[0], "rb") as probe:
            n_channels  = probe.getnchannels()
            sample_rate = probe.getframerate()
            sampwidth   = probe.getsampwidth()   # bytes per sample per channel

        print(f">>> sampwidth: {sampwidth}, sample_rate: {sample_rate}, n_channels: {n_channels}")

        # Map wave sampwidth → ffmpeg pcm codec
        pcm_codec = {1: "u8", 2: "s16le", 3: "s24le", 4: "s32le"}
        if sampwidth not in pcm_codec:
            raise ValueError(f"Unsupported sample width: {sampwidth} bytes")

        # --- Open ffmpeg process that reads raw PCM from stdin ---------------
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",                              # overwrite output
            "-f",          pcm_codec[sampwidth],
            "-ar",         str(sample_rate),
            "-ac",         str(n_channels),
            "-i",          "pipe:0",           # read PCM from stdin
            "-c:a",        "libmp3lame",
            "-b:a",        f"{bitrate}k",
            output_mp3,
        ]

        proc = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        def feed(data: bytes) -> None:
            """Write bytes to ffmpeg stdin, propagating broken-pipe errors clearly."""
            try:
                proc.stdin.write(data)
            except BrokenPipeError:
                stderr = proc.stderr.read().decode(errors="replace")
                raise RuntimeError(f"ffmpeg pipe broke:\n{stderr}")

        try:
            for file_index, path in enumerate(paths):
                # --- Validate subsequent files match the first -----------------
                with wave.open(path, "rb") as wf:
                    if wf.getnchannels() != n_channels:
                        raise ValueError(
                            f"{path}: expected {n_channels} channels, "
                            f"got {wf.getnchannels()}"
                        )
                    if wf.getframerate() != sample_rate:
                        raise ValueError(
                            f"{path}: expected {sample_rate} Hz, "
                            f"got {wf.getframerate()} Hz"
                        )
                    if wf.getsampwidth() != sampwidth:
                        raise ValueError(
                            f"{path}: expected {sampwidth}-byte samples, "
                            f"got {wf.getsampwidth()}"
                        )

                    # Stream PCM frames in chunks
                    while True:
                        frames = wf.readframes(chunk_frames)
                        if not frames:
                            break
                        feed(frames)

                # Insert silence between files (not after the last one)
                if wav_pauses_sec_between is not None and file_index < len(paths) - 1:
                    silence_seconds = wav_pauses_sec_between[file_index]
                    silence_frames = int(math.ceil(silence_seconds * sample_rate))
                    silence_block  = b"\x00" * (silence_frames * n_channels * sampwidth)
                    
                    feed(silence_block)

            proc.stdin.close()
            proc.wait()

        except Exception:
            proc.stdin.close()
            proc.kill()
            proc.wait()
            raise

        if proc.returncode != 0:
            stderr = proc.stderr.read().decode(errors="replace")
            raise RuntimeError(f"ffmpeg exited with code {proc.returncode}:\n{stderr}")