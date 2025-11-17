import sys
sys.path.insert(0, r'C:\Users\wwwch\AppData\Roaming\Python\Python314\site-packages')

# Try to import specific whisper components to see what works
try:
    import whisper
    print('Full whisper import successful')
except ImportError as e:
    print(f'Full whisper import failed: {e}')

    # Try importing specific parts
    try:
        from whisper import load_model
        print('load_model import successful')
    except ImportError as e:
        print(f'load_model import failed: {e}')

    try:
        from whisper import transcribe
        print('transcribe import successful')
    except ImportError as e:
        print(f'transcribe import failed: {e}')

# Check what whisper version we have
try:
    import whisper
    print(f'Whisper version: {whisper.__version__}')
except:
    print('Cannot get whisper version')

# Try to load model to see if numba is really needed
try:
    import whisper
    print("Attempting to load tiny model (will fail during import if numba required)")
    model = whisper.load_model("tiny", download_root="./models")
    print("Model loaded successfully!")
except Exception as e:
    print(f"Model loading error: {e}")
