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
            return False

        y_stretched = librosa.effects.time_stretch(y, rate=rate)

        #sf.write(output_path, y_stretched, sr)
        sf.write(output_path, y_stretched, sr, format="WAV") #TODO: format should be the same as input not "WAV"

        return True

    @staticmethod
    def get_duration(input_path):
        return librosa.get_duration(path=input_path)