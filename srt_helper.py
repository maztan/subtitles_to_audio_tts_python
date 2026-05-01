from dataclasses import dataclass

@dataclass
class SubtitleBlock:
    """Subtitle block from an .srt file.

    Attributes:
        index (int): Sequence number.
        start (float): Start time in seconds.
        end (float): End time in seconds.
        text (str): Subtitle text content.
    """
    index: int
    start: float
    end: float
    text: str


def stream_srt(path):
    with open(path, "r", encoding="utf-8") as f:
        block = []

        for line in f:
            line = line.rstrip("\n")

            if line == "":
                if block:
                    yield parse_block(block)
                    block = []
            else:
                block.append(line)

        if block:
            yield parse_block(block)

def parse_num_seconds(time_str):
    # time is in the format 00:00:07,549 (hh:mm:ss,ms)
    hh, mm, ss_ms = time_str.split(":")
    ss, ms = ss_ms.split(",")
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000

def parse_block(block):
    idx = int(block[0])
    # time is in the format 00:00:07,549 (hh:mm:ss,ms)
    start, end = block[1].split(" --> ")

    start = parse_num_seconds(start)
    end = parse_num_seconds(end)

    text = "\n".join(block[2:])

    return SubtitleBlock(idx, start, end, text)