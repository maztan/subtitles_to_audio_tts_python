from audio_helper import AudioHelper
from srt_helper import stream_srt
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

    prev_block = None
    num_small_gaps = 0
    total_blocks = 0

    max_count = 10

    tts = GoogleGeminiTTS()

    for block in stream_srt(r"C:\Users\savai\Desktop\TorrentDownloads\Kikis Delivery Service (1989) [1080p] [BluRay] [YTS.MX]\Kikis.Delivery.Service.1989.1080p.BluRay.x264.AAC-[YTS.MX].srt"):
        total_blocks += 1
        if prev_block is not None:
            # If the gap between blocks is small, consider merging them
            if prev_block.end + 1 > block.start:
                print(f"GAP IS SMALL {block.start - prev_block.end} sec")
                num_small_gaps += 1
        prev_block = block
        #print(block)

        audio_bytes = await tts.synthesize(block.text)

        block_duration = block.end - block.start
        audio_duration = AudioHelper.get_duration(audio_bytes)

        print(f"Block duration: {block_duration:.2f} sec, Audio duration: {audio_duration:.2f} sec")

        max_count -= 1
        if max_count <= 0:
            break

    print(f"Total small gaps found: {num_small_gaps}")
    print(f"Total blocks found: {total_blocks}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())