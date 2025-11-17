deps = ['torch', 'numpy', 'openai-whisper']
for dep in deps:
    try:
        __import__(dep)
        print(f'{dep}: installed')
    except ImportError:
        print(f'{dep}: not installed')
