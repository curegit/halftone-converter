import argparse as arg
from math import sqrt, sin, acos, pi

def make_occupancy(pitch):
	def occupancy(radius):
		if radius < 0:
			return 0.0
		elif radius < pitch / 2:
			return pi * radius ** 2 / pitch ** 2
		elif radius < sqrt(2) / 2 * pitch:
			theta = acos(pitch / (2 * radius))
			return (radius / pitch) ** 2 * (pi - 4 * theta) + 2 * radius * sin(theta) / pitch
		else:
			return 1.0
	return occupancy

def radius_table(pitch, depth):
	color = 0
	occupancy = 0.0
	f = make_occupancy(pitch)
	while occupancy <= pi / 4:
		yield pitch * sqrt(occupancy / pi)
		color += 1
		occupancy = color / (depth - 1)
	r = 2 / pitch
	while color < depth - 1:
		while f(r) < occupancy:
			r += 0.0000001
		yield r
		color += 1
		occupancy = color / (depth - 1)
	yield sqrt(2) / 2 * pitch

def make_radius(pitch, depth):
	table = list(radius_table(pitch, depth))
	def radius(occupancy):
		if occupancy < 0:
			return 0.0
		elif occupancy >= depth:
			return sqrt(2) / 2 * pitch
		else:
			return table[occupancy]
	return radius

'''
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
'''
