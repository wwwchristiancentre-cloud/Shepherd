try:
    import whisper
    print('Whisper available')
except ImportError:
    print('Whisper not installed')
