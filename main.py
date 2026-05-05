from io import BytesIO
import os

from audio_helper import AudioHelper
from misc_utils import remove_tags, reset_dir
from srt_helper import SubtitleBlock, stream_srt
from tts.plugins.google_gemini_tts import GoogleGeminiTTS
from tts.plugins.sapi_tts import print_sapi_voices
from tts.plugins.winrt_tts import WinRTTTS

async def main():
    # tts = WinRTTTS()
    # audio_data = await tts.synthesize("Hello from Windows WinRT text to speech")
    # mp3_bytes = tts.wav_to_mp3(audio_data)

    # with open("output.mp3", "wb") as f:
    #     f.write(mp3_bytes)
    # return

    #print_sapi_voices()

# GOOGLE TTS TEST------
    #tts = GoogleGeminiTTS()
    #tts.list_models()
    #await tts.synthesize("Hello from Google Gemini text to speech")
#----------------------

    #tts = GoogleGeminiTTS()
    tts = WinRTTTS()

    reset_dir("audio_output")

#------------------

    async def process_block(block: SubtitleBlock, output_path: str) -> float:
        """
        Synthesize audio for a subtitle block and save it to the specified output path.

        Returns:
            The duration of the synthesized audio in seconds.
        """
        clean_text = remove_tags(block.text)
        audio_bytes = await tts.synthesize(clean_text)

        block_duration = block.end - block.start
        #audio_duration = AudioHelper.get_duration(BytesIO(audio_bytes))

        # audio bytes matching the block duration (shortened or keept as is)

        audio_len_matched, was_shortened = AudioHelper.shorten_to_duration(BytesIO(audio_bytes), target_seconds=block_duration, output_format="WAV")
        print(f"Audio was shortened: {was_shortened}")

        #DEBUG:
        #with open(f"audio_output/output_{count}.wav", "wb") as f:
        with open(output_path, "wb") as f:
            f.write(audio_len_matched.getvalue())
        #----------

        print(f"Otput block {count} text: {block.text}")
        print(f"Otput block {count} duration: {block_duration:.2f} sec, Audio duration: {audio_duration:.2f} sec, new duration: {new_audio_duration:.2f} sec\n")

        out_audio_duration = AudioHelper.get_duration(audio_len_matched)
        return out_audio_duration

    max_gap_seconds = 1.0
    prev_block = None
    output_path_template = "audio_output/output_{}.wav"
    count = 0
    total_input_blocks = 0
    total_merged_blocks = 0
    silences_after_blocks = [] # no silence after the last (TODO:OR BEFORE FIRST BLOCK? - maybe add the before??)

    DEBUG_MAX_COUNT = 10
    i = 0
    for block in stream_srt(r"C:\Users\savai\Desktop\TorrentDownloads\Kikis Delivery Service (1989) [1080p] [BluRay] [YTS.MX]\Kikis.Delivery.Service.1989.1080p.BluRay.x264.AAC-[YTS.MX].srt"):
        i += 1

        total_input_blocks += 1
        #TODO: add max consecutive blocks merged?
        #TODO: AUDIO LENGHT DOES NOT MATCH THE BLOCK DURATION
        if prev_block is not None:
            # Check for (wrong) overlapping blocks (negative gap)
            if prev_block.end > block.start:
                print(f"WARNING: Detected overlapping blocks. Latter block will be skipped."
                      f"Previous block end time {prev_block.end} is greater than current block start time {block.start}. "
                      f"This may indicate an issue with the subtitle file. Consider reviewing the SRT file for potential errors.")
                continue

            # If the gap between blocks is small, merge them
            if prev_block.end + max_gap_seconds > block.start:
                prev_block.end = block.end  # Extend the previous block's end time to merge with the current block
                prev_block.text += " " + block.text
                total_merged_blocks += 1
                # count stays the same since we are merging into the previous block
            else:
                # Process the previous block (synthesize audio)
                audio_duration = await process_block(prev_block, output_path_template.format(count))

                # The difference in seconds between block length and the corresponding audio lenght (meaning, how much silenece we need after this block)
                diff_subtitle_audio = (prev_block.end - prev_block.start) - audio_duration
                if diff_subtitle_audio < 0:
                    print(f"WARNING: Audio duration is longer than subtitle block duration by {diff_subtitle_audio:.2f} seconds. Consider reviewing the SRT file for potential errors.")
                    diff_subtitle_audio = 0
                else: # diff_subtitle_audio >= 0
                    silences_after_blocks.append(diff_subtitle_audio)

                prev_block = block
                count += 1
        else:
            prev_block = block

        if i >= DEBUG_MAX_COUNT:
            print(f"DEBUG: Reached max count of {DEBUG_MAX_COUNT}, stopping subtitle processing.")
            break
    
    # prev_block, if it exists, is not processed
    # as it could have been assigned only when there was a next block
    # or there was only one block in total
    # in both cases, it was not processed at this point.
    if prev_block is None:
        print("WARNING: No subtitle blocks found to process.")
    else:
        audio_duration = await process_block(prev_block, output_path_template.format(count))

        print("Joining all generated wav files into a single mp3....")
        wav_paths=[f"audio_output/{f}" for f in sorted(os.listdir("audio_output")) if f.endswith(".wav")]
        AudioHelper.join_wavs_to_mp3(
            wav_paths=wav_paths,
            wav_pauses_sec_between=[2] * (len(wav_paths) - 1),  # 2 second of silence between each file
            output_mp3="final_output.mp3",
            silence_seconds=0.5,
            bitrate=128,
        )

    print(f"Total input blocks found: {total_input_blocks} (of which {total_merged_blocks} were merged due to short gaps)")
    print("DONE")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())