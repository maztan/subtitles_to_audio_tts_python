from srt_helper import stream_srt

async def main():
    for block in stream_srt(r"C:\Users\savai\Desktop\TorrentDownloads\Kikis Delivery Service (1989) [1080p] [BluRay] [YTS.MX]\Kikis.Delivery.Service.1989.1080p.BluRay.x264.AAC-[YTS.MX].srt"):
        print(block)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())