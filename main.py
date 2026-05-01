from srt_helper import stream_srt
from tts_api import test_tts

async def main():
    test_tts()
    return
    prev_block = None
    num_small_gaps = 0
    total_blocks = 0

    for block in stream_srt(r"C:\Users\savai\Desktop\TorrentDownloads\Kikis Delivery Service (1989) [1080p] [BluRay] [YTS.MX]\Kikis.Delivery.Service.1989.1080p.BluRay.x264.AAC-[YTS.MX].srt"):
        total_blocks += 1
        if prev_block is not None:
            # If the gap between blocks is small, consider merging them
            if prev_block.end + 1 > block.start:
                print(f"GAP IS SMALL {block.start - prev_block.end} sec")
                num_small_gaps += 1
        prev_block = block
        print(block)

    print(f"Total small gaps found: {num_small_gaps}")
    print(f"Total blocks found: {total_blocks}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())