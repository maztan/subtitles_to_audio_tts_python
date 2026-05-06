Converts SRT subtitles into audio track. Supports WinRT TTS, will support Google Gemini.
Plugins are easy to add for anyone interested in creating one for their own needs.

Requires ffmpeg installed on the OS.



Info only for the dev:

#See https://pypi.org/project/py3-tts-wrapper/
pip install "py3-tts-wrapper[sapi]"

#Install optional MP3 codec support:
pip install "py3-tts-wrapper[mp3]"


TODO: merge subs with small gaps between
the audio resulting from merged blocks can take entire time from start to end of merged blocks

TODO: consider adding https://github.com/rany2/edge-tts

TODO: semantic subtitle splitting, not based on blocks; this would need "full sentence detection", probably can be done with a language model (aka "AI")

TODO: write debug of audio blocks starts and ends and where the pauses were inserted and how long they were