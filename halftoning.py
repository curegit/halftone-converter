import argparse as arg
import htfunctions as ht

def make_fill_rate(pitch):
    def func(radius):
        if radius < 0:
            return 0.0
        elif radius < pitch / 2:
            return radius * radius * pi / (pitch * pitch)
        elif radius < sqrt(2.0) * pitch / 2:
            return (radius * radius * pi - 4 * radius * radius * acos(pitch / (2 * radius)) + 2 * pitch * radius * sin(acos(pitch / (2 * radius)))) / (pitch * pitch)
        else:
            return 1.0
    return func

def make(pitch, s=256):
    table = []
    f = make_fill_rate(pitch)
    r = 0.0
    d = 0.0001
    while True:
        #rn = r + d
        if f(r) >= len(table) / (s-1):
            table.append(r)
        r += d
        if len(table) == s:
            break
    def h(v):
        if v < 0:
            return 0.0
        if v >= s:
            return math.sqrt(2.0) * pitch / 2.0
        else:
            return table[v]
    return h

# コマンドライン引数をパース
parser = arg.ArgumentParser(allow_abbrev=False, description="Halftoning ")
parser.add_argument("images", metavar="FILE", nargs="+", help="")
parser.add_argument("-d", "--directory", help="")
parser.add_argument("-rp", "--rgb-profile", help="")
parser.add_argument("-cp", "--cmyk-profile", help="")
parser.add_argument("-p", "--prefix", help="")
parser.add_argument("-s", "--suffix", help="")
parser.add_argument("-c", "--cmyk", action="store_true", help="")
parser.add_argument("-l", "--layers", action="store_true", help="")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-e", "--enumerate", action="store_true", help="")
args = parser.parse_args()

# debug
print(vars(args))
print(args.directory)

# 引数のバリデーションと展開
directory = args.directory if args.direcotry != None else ""
rgb_profile = args.
cmyk_profile = 
force = args.force

radius
pitch
c = 
m =
y = 
k =

# 出力ディレクトリの確認

#
for (i, image) in enumerate(images):
