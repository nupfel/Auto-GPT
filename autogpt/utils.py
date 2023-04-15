import yaml
from colorama import Fore
import struct
from pvrecorder import PvRecorder
import regex_spm
from time import sleep
import wave
import openai
from config import Config
from spinner import Spinner
import orangepi.lite
from OPi import GPIO

cfg = Config()

openai.api_key = cfg.openai_api_key

WAVE_OUTPUT_FILENAME = "recording.wav"

BUTTON_PIN = 18
GPIO.setmode(orangepi.lite.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN)

def record_audio():
    CHUNK = 512
    recorder = PvRecorder(device_index=1, frame_length=CHUNK)
    audio = []
    CHANNELS = 1
    RATE = 16000

    try:
        recorder.start()

        while GPIO.input(BUTTON_PIN):
            frame = recorder.read()
            audio.extend(frame)

#    except KeyboardInterrupt:
        recorder.stop()
        with wave.open(WAVE_OUTPUT_FILENAME, 'w') as f:
            f.setparams((CHANNELS, 2, RATE, CHUNK, "NONE", "NONE"))
            f.writeframes(struct.pack('h' * len(audio), *audio))
            f.close()

    finally:
        recorder.delete()

    return WAVE_OUTPUT_FILENAME


def transcribe_audio(audio_file):
    with open(audio_file, 'rb') as f:
        response = openai.Audio.transcribe("whisper-1", f)
        transcript = response.text.strip()
        return transcript
    return


def clean_input(prompt: str=''):
    print(prompt)

    while not GPIO.input(BUTTON_PIN):
        sleep(0.05)

    with Spinner('RECORDING'):
        audio_file = record_audio()
        transcript = transcribe_audio(audio_file)
        print(transcript)

    match regex_spm.fullmatch_in(transcript):
        case r'((?i)nothing|empty)':
            return ""

        case r'((?i)cancel|exit|quit)':
            print("You interrupted Auto-GPT")
            print("Quitting...")
            exit(0)

    return transcript


def validate_yaml_file(file: str):
    try:
        with open(file, encoding="utf-8") as fp:
            yaml.load(fp.read(), Loader=yaml.FullLoader)
    except FileNotFoundError:
        return (False, f"The file {Fore.CYAN}`{file}`{Fore.RESET} wasn't found")
    except yaml.YAMLError as e:
        return (
            False,
            f"There was an issue while trying to read with your AI Settings file: {e}",
        )

    return (True, f"Successfully validated {Fore.CYAN}`{file}`{Fore.RESET}!")
