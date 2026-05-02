import win32com.client

def print_sapi_voices():
    voice = win32com.client.Dispatch("SAPI.SpVoice")

    for i, v in enumerate(voice.GetVoices()):
        print(i, v.GetDescription())