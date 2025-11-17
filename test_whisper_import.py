import sys
sys.path.insert(0, r'C:\Users\wwwch\AppData\Roaming\Python\Python314\site-packages')
try:
    import whisper
    print('Whisper import successful')
except Exception as e:
    print(f'Error: {e}')
