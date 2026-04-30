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


def parse_block(block):
    idx = int(block[0])
    start, end = block[1].split(" --> ")
    text = "\n".join(block[2:])

    return {
        "index": idx,
        "start": start,
        "end": end,
        "text": text
    }