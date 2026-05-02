import librosa
import soundfile as sf

class AudioHelper:
    @staticmethod
    def shorten_to_duration(input_path, output_path, target_duration):
        y, sr = librosa.load(input_path, sr=None)

        current_duration = len(y) / sr

        rate = current_duration / target_duration

        if rate < 1.0:
            print(f"Audio is shorter than target duration. No processing needed.")
            return

        y_stretched = librosa.effects.time_stretch(y, rate=rate)

        sf.write(output_path, y_stretched, sr)

    @staticmethod
    def get_duration(input_path):
        return librosa.get_duration(filename=input_path)