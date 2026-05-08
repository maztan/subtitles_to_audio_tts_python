from io import BytesIO
import os

from audio_helper import AudioHelper
from misc_utils import remove_tags, reset_dir
from srt_helper import SubtitleBlock, stream_srt

from tts.plugins.google_gemini_tts import GoogleGeminiTTS
from tts.plugins.sapi_tts import print_sapi_voices
from tts.plugins.winrt_tts import WinRTTTS
from tts.plugins.msedge_tts import MSEdgeTTS

from dotenv import load_dotenv
load_dotenv()

async def main():
    # tts = WinRTTTS()
    # audio_data, audio_format = await tts.synthesize("Hello from Windows WinRT text to speech")
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
    #tts = WinRTTTS()
    tts = MSEdgeTTS()

    #await tts.list_voices()
    #return

    reset_dir("audio_output")

    #TEST
    # audio_bytes, audio_format = await tts.synthesize("This is a test of the text to speech API.")
    # with open(f"audio_output/test.{audio_format.lower()}", "wb") as f:
    #     f.write(audio_bytes)
    # print(f"Test synthesis complete, audio saved to audio_output/test.{audio_format.lower()}")
    # return

#------------------

    async def process_block(block: SubtitleBlock, output_path: str) -> float:
        """
        Synthesize audio for a subtitle block and save it to the specified output path.

        Returns:
            The duration of the synthesized audio in seconds.
        """
        clean_text = remove_tags(block.text)
        audio_bytes, audio_format = await tts.synthesize(clean_text)

        #---------------------
        # convert to wav if necessary; we can only add silence if we have wav (pcm) audio
        if(audio_format != "WAV"):
            print(f"Converting synthesized audio from {audio_format} to WAV format for block {count}...")
            if audio_format == "MP3":
                audio_bytes = AudioHelper.mp3_to_wav(audio_bytes)
            else:
                raise ValueError(f"Unsupported audio format: {audio_format}")

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

        out_audio_duration = AudioHelper.get_duration(audio_len_matched)

        #if __debug__:

        return out_audio_duration

    # log file holding information about how the blocks were converted to audio
    # and the timings of the audio and sileneces placed
    
    # if gap is shorter than this, the blocks will be merged before synthesizing of audio
    MERGE_NEARBY_BLOCKS = False
    MAX_GAP_SECONDS = 0.5

    prev_block = None
    output_path_template = "audio_output/output_{}.wav"
    count = 0
    total_merged_blocks = 0

    output_audio_paths = []
    silences_after_blocks = [] # no silence after the last (TODO:OR BEFORE FIRST BLOCK? - maybe add the before??)

    print("Will try to merge nearby blocks with gap shorter than ", MAX_GAP_SECONDS, " seconds") if MERGE_NEARBY_BLOCKS else print("Will not merge nearby blocks")
    
    DEBUG_MAX_COUNT = 20
    block_i = 0
    for block in stream_srt(r"C:\Users\savai\Desktop\TorrentDownloads\Kikis Delivery Service (1989) [1080p] [BluRay] [YTS.MX]\Kikis.Delivery.Service.1989.1080p.BluRay.x264.AAC-[YTS.MX].srt"):
        #TODO: add max consecutive blocks merged?
        if prev_block is not None:
            # Check for (wrong) overlapping blocks (negative gap)
            if prev_block.end > block.start:
                print(f"WARNING: Detected overlapping blocks. Latter block will be skipped."
                      f"Previous block end time {prev_block.end} is greater than current block start time {block.start}. "
                      f"This may indicate an issue with the subtitle file. Consider reviewing the SRT file for potential errors.")
                continue

            # If the gap between blocks is small, merge them
            if MERGE_NEARBY_BLOCKS and prev_block.end + MAX_GAP_SECONDS > block.start:
                prev_block.end = block.end  # Extend the previous block's end time to merge with the current block
                prev_block.text += " " + block.text
                total_merged_blocks += 1
                # count stays the same since we are merging into the previous block
                #update log
                print(f"blocks merged: new blocks span {prev_block.start} -> {prev_block.end}\n");
            else:
                # Process the previous block (synthesize audio)
                output_path = output_path_template.format(count)
                audio_duration = await process_block(prev_block, output_path)
                output_audio_paths.append(output_path)

                # we need to fill with audio the space of entire block + the gap until the next block
                # to keep audio in sync thus we need to pad with silence until the start of the next block 
                diff_subtitle_audio = block.start - (prev_block.start + audio_duration)
                if diff_subtitle_audio < 0:
                    print(f"WARNING: Audio duration is longer than subtitle block duration by {diff_subtitle_audio:.2f} seconds. Consider reviewing the SRT file for potential errors.")
                    diff_subtitle_audio = 0 #reset to zero toavoid negative silence length value
                
                silences_after_blocks.append(diff_subtitle_audio)

                print(f"Otput block {count} text: {block.text}")
                print(f"Otput block {count} duration: {prev_block.end - prev_block.start:.2f} sec, out audio duration: {audio_duration:.2f} sec, silence: {diff_subtitle_audio:.2f} sec (total: {audio_duration + diff_subtitle_audio:.2f} ?= block time till next block {block.start - prev_block.start:.2f} sec)\n")

                prev_block = block
                count += 1
        else:
            prev_block = block

        if block_i >= DEBUG_MAX_COUNT:
            print(f"DEBUG: Reached max count of {DEBUG_MAX_COUNT}, stopping subtitle processing.")
            break
        block_i += 1
    
    # prev_block, if it exists, is not processed
    # as it could have been assigned only when there was a next block
    # or there was only one block in total
    # in both cases, it was not processed at this point.
    if prev_block is None:
        print("WARNING: No subtitle blocks found to process.")
    else:
        output_path = output_path_template.format(count)
        audio_duration = await process_block(prev_block, output_path)
        output_audio_paths.append(output_path)

        print(f"Otput block {count} text: {block.text}")
        print(f"Otput block {count} span {prev_block.start} -> {prev_block.end} duration: {prev_block.end - prev_block.start:.2f} sec, out audio duration: {audio_duration:.2f} sec\n")
        block_i += 1
        # no silence after the last block, so we don't push to silences_after_blocks

        FINAL_OUTPUT_FILE_NAME = "final_output.mp3"
        print(f"Joining all generated wav files into a single mp3 {FINAL_OUTPUT_FILE_NAME}....")
        #wav_paths=[f"audio_output/{f}" for f in sorted(os.listdir("audio_output")) if f.endswith(".wav")]

        assert len(output_audio_paths) == len(silences_after_blocks) + 1, f"Number of wav files ({len(output_audio_paths)}) should be one more than the number of silences ({len(silences_after_blocks)}) since there is no silence after the last block."

        AudioHelper.join_wavs_to_mp3(
            wav_paths=output_audio_paths,
            wav_pauses_sec_between=silences_after_blocks, #[2] * (len(wav_paths) - 1),  # 2 second of silence between each file
            output_mp3=FINAL_OUTPUT_FILE_NAME,
            bitrate=128,
        )

    print(f"Total input blocks found: {block_i} (of which {total_merged_blocks} were merged due to short gaps)")

    print("DONE")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())