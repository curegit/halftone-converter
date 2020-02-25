import sys
import os
import os.path
import inspect

# 標準エラー出力にプリントする
def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

# ディレクトリが無ければ再帰的に作成する
def mkdirp(path):
	os.makedirs(path, exist_ok=True)

# ディレクトリ、ファイル名、拡張子からパスを構築する
def filepath(dirpath, filename, ext):
	p = os.path.join(dirpath, filename) + os.extsep + ext
	return os.path.normpath(p)

# 呼び出し元のスクリプトからの相対パスを構築する
def filerelpath(relpath):
	f = inspect.stack()[1].filename
	d = os.getcwd() if f == "<stdin>" else os.path.dirname(f)
	return os.path.join(d, relpath)

# パスにファイルがすでに存在したら別のファイル名にしたパスを返す
def altfilepath(path, prefix="_"):
	while os.path.lexists(path):
		root, ext = os.path.splitext(path)
		head, tail = os.path.split(root)
		path = os.path.join(head, prefix + tail) + ext
	return path
