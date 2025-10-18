__version__ = "2.6.9"

def pyinstaller_hooks_dir():
	from pathlib import Path
	return [str(Path(__file__).with_name("pyinstaller").resolve())]
