from argparse import ArgumentParser
from PIL import Image, ImageCms
from functions import halftone_image

# コマンドライン引数をパース
parser = arg.ArgumentParser(allow_abbrev=False, description="Halftoning ")
parser.add_argument("images", metavar="FILE", nargs="+", help="")
parser.add_argument("-d", "--directory", help="")
parser.add_argument("-p", "--prefix", help="")
parser.add_argument("-s", "--suffix", help="")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-e", "--enumerate", action="store_true", help="")
parser.add_argument("-c", "--cmyk", action="store_true", help="")
parser.add_argument("-b", "--bands", action="store_true", help="")
parser.add_argument("-ip", "--input-profile", help="")
parser.add_argument("-cp", "--cmyk-profile", help="")
parser.add_argument("-op", "--output-profile", help="")
parser.add_argument("-ig", "--ignore-embedded-profile", help="")
parser.add_argument("-kc", "--keep-cyan", action="store_true", help="")
parser.add_argument("-km", "--keep-magenta", action="store_true", help="")
parser.add_argument("-ky", "--keep-yellow", action="store_true", help="")
parser.add_argument("-kk", "--keep-key", action="store_true", help="")
parser.add_argument("-kb", "--keep-black", action="store_true", help="")
parser.add_argument("-nb", "--no-blur", action="store_true", help="")
parser.add_argument("-bb", "--box-blur", action="store_true", help="")
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

for i in range(0, 3):
	img = Image.open("i2.jpg")
	cmyk = ImageCms.profileToProfile(img, 'sRGB Color Space Profile.icm', 'JapanColor2011Coated.icc', renderingIntent=i, outputMode='CMYK')

	rgb = ImageCms.profileToProfile(cmyk, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"h-cmyk-{i}to3.png")

	c, m, y, k = cmyk.split()

	nc = halftone_image(c, 2, 15, scale=2)
	nm = halftone_image(m, 2, 75, scale=2)
	ny = halftone_image(y, 2, 35, scale=2)
	nk = halftone_image(k, 2, 45, scale=2)

	img = Image.merge("CMYK", [nc, nm, ny, nk])
	rgb = ImageCms.profileToProfile(img, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"h-out{i}to3.png")

for i in range(0, 3):
	img = Image.open("588908_1_20190215131009_800_800.png")
	cmyk = ImageCms.profileToProfile(img, 'sRGB Color Space Profile.icm', 'JapanColor2011Coated.icc', renderingIntent=i, outputMode='CMYK')

	rgb = ImageCms.profileToProfile(cmyk, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"b-h-cmyk-{i}to3.png")

	c, m, y, k = cmyk.split()

	nc = halftone_image(c, 2, 15, scale=2)
	nm = halftone_image(m, 2, 75, scale=2)
	ny = halftone_image(y, 2, 35, scale=2)
	nk = halftone_image(k, 2, 45, scale=2)

	img = Image.merge("CMYK", [nc, nm, ny, nk])
	rgb = ImageCms.profileToProfile(img, 'JapanColor2011Coated.icc', 'sRGB Color Space Profile.icm', renderingIntent=3, outputMode='RGB')
	rgb.save(f"b-h-out{i}to3.png")
