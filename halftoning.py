from argparse import ArgumentParser
from PIL import Image, ImageCms
from utilities import mkdirp, filepath, filerelpath, altfilepath
from functions import halftone_grayscale_image, halftone_cmyk_image, make_profile_transform

# コマンドライン引数をパース
parser = ArgumentParser(allow_abbrev=False, description="Halftoning ")
parser.add_argument("images", metavar="FILE", nargs="+", help="")
parser.add_argument("-d", "--directory", help="")
parser.add_argument("-p", "--prefix", help="")
parser.add_argument("-s", "--suffix", help="")
parser.add_argument("-f", "--force", action="store_true", help="")
parser.add_argument("-e", "--enumerate", action="store_true", help="")
parser.add_argument("-c", "--cmyk", action="store_true", help="")
parser.add_argument("-b", "--bands", action="store_true", help="")
parser.add_argument("-x", "--pitch", action="store_true", help="")
parser.add_argument("-a", "--angles", metavar="C,M,Y,K", help="")
parser.add_argument("-ip", "--input-profile", help="")
parser.add_argument("-cp", "--cmyk-profile", help="")
parser.add_argument("-op", "--output-profile", help="")
parser.add_argument("-ig", "--ignore-embedded-profile", action="store_true", help="")
parser.add_argument("-kc", "--keep-cyan", action="store_true", help="")
parser.add_argument("-km", "--keep-magenta", action="store_true", help="")
parser.add_argument("-ky", "--keep-yellow", action="store_true", help="")
parser.add_argument("-kk", "--keep-key", action="store_true", help="")
parser.add_argument("-kb", "--keep-black", action="store_true", help="")
parser.add_argument("-nb", "--no-blur", action="store_true", help="")
parser.add_argument("-bb", "--box-blur", action="store_true", help="")
parser.add_argument("-gb", "--gaussian-blur", action="store_true", help="")
args = parser.parse_args()

# debug
print(vars(args))
print(args.directory)

# 引数のバリデーションと展開
#directory = args.directory if args.direcotry != None else ""
#rgb_profile = args
#cmyk_profile =
#force = args.force

pitch = 2
keep_flags = (args.keep_cyan, args.keep_magenta, args.keep_yellow, args.keep_key or args.keep_black)

if len([f for f in [args.no_blur, args.box_blur, args.gaussian_blur] if f]) > 1:
	print("")
	exit()
blur = None if args.no_blur else "box" if args.box_blur else "gaussian"

# 出力ディレクトリの確認

out_cmyk = False

cmyk_initent = 1
rgb_intent = 3


in_profile = ImageCms.createProfile("sRGB")
cmyk_profile = "profile/JapanColor2011Coated.icc"
out_profile = in_profile

ignore_profile = args.ignore_embedded_profile

srgb =

pt_cmyk = make_profile_transform((in_profile, cmyk_profile), ("RGB", "CMYK"), cmyk_initent, not ignore_profile)
pt_rgb = make_profile_transform((cmyk_profile, out_profile), ("CMYK", "RGB"), rgb_intent, False)


# メインループ
n = len(args.images)
for i, f in enumerate(args.images, 1):
	try:
		img = Image.open(f)
		if img.mode == "L":
			pass
		elif img.mode == "CMYK":
			pass
		elif img.mode == "RGB":
			cmyk = pt_cmyk(img)
			cmyk.save(f"{i}.tiff")
			halftone = halftone_cmyk_image(cmyk, pitch, blur=blur, keep_flags=keep_flags)
			if out_cmyk:
				halftone.save(f"{i}.png")
			else:
				pt_rgb(halftone).save(f"{i}.png")
		else:
			pass
		print(f"{i} / {n} Done")
	except:
		print(f"{i} / {n} Error")
