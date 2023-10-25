# Halftone Converter

An image converter to generate halftone images of high quality

## Features

- Make your images halftones easily
- High-quality rendering by Cairo graphics library
- Halftones of 3 color types – Gray, RGB, and CMYK
- Color space transform with ICC profiles

![Colorful Play Balls](images/colorful-play-balls.png)

## Requirements

This application can be run by Python3 on any OS.
Note that [Pycairo requires Cairo core library](https://pycairo.readthedocs.io/en/latest/getting_started.html).

- Python >= 3.7
- NumPy >= 1.17
- Pillow >= 8.2
- Pycairo >= 1.20

### Install Pycairo on macOS

```sh
brew install py3cairo
```

### Install Pycairo on Windows

```ps
pip install pycairo
```

```ps
conda install pycairo
```

## Usage

The application takes image files as input and outputs halftones as image files.
It has command line interface shown as below.

```sh
python3 halftone.py [-h] [-q] [-e] [-g] [-f] [-d DIR] [-P PREFIX] [-S SUFFIX]
                    [-E [START]] [-p PX] [-x SCALE] [-b {none,box,gaussian}]
                    [-A DEG] [-t DEG DEG DEG] [-a DEG DEG DEG DEG]
                    [-m {auto,gray,rgb,cmyk}] [-o {auto,gray,rgb,cmyk}] [-T]
                    [-G GRAY_ICC_FILE] [-I RGB_ICC_FILE] [-M CMYK_ICC_FILE]
                    [-L GRAY_ICC_FILE] [-l {per,sat,rel,abs,0,1,2,3}]
                    [-R RGB_ICC_FILE] [-r {per,sat,rel,abs,0,1,2,3}]
                    [-C CMYK_ICC_FILE] [-c {per,sat,rel,abs,0,1,2,3}] [-H]
                    [--ignore] [--discard] [--naive] [--gamma-correction]
                    [--key RATE] [-K] [--keep-red] [--keep-green] [--keep-blue]
                    [--keep-cyan] [--keep-magenta] [--keep-yellow] [--keep-key]
                    FILE [FILE ...]
```

### Positional Arguments

#### FILE

describe input image files (required), can be multiple

Input images' formats are limited to what Pillow can read.
Also, their color spaces must be Gray (L, grayscale), LA (grayscale with alpha), RGB, RGBA, P (GIF, transparent images), or CMYK.

### Optional Arguments

#### -h, --help

show the help message and exit

#### -q, --quiet

suppress non-error messages

#### -e, --exit

stop the program immediately by an error even if jobs remain

By default, it skips failed jobs and starts the next jobs.

#### -g, --glob

interpret `FILE` values as glob patterns (e.g., `*.png`, `**/*.jpg`)

Use this option if the shell's wildcard expansion is not available and enough.
Pattern `**` matches any files and zero or more directories recursively.
This glob function will include hidden files and directories.

#### -f, --force

overwrite existing files by outputs

By default, an alternate filename will be used if the original filename conflicts.

#### -d DIR, --directory DIR

save output images in `DIR` directory

The directory will be created automatically if it does not exist.

#### -P PREFIX, --prefix PREFIX

specify a prefix string of output filenames

#### -S SUFFIX, --suffix SUFFIX

specify a suffix string of output filenames

#### -E [START], --enumerate [START]

use consecutive numbers as output filenames

It counts up by one from `START`.
The default `START` is 1.

#### -p PX, --pitch PX, --interval PX

arrange halftone dots at intervals of `PX` pixels in input images

Change this value for desired results.
The default value is 4.0.

#### -x SCALE, -s SCALE, --scale SCALE

the scale factor of output images to input images

The default value is 1.0.

#### -b {none,box,gaussian}, --blur {none,box,gaussian}

blur type to calculate the mean of pixels

The default is `gaussian`.

#### -A DEG, --angle DEG, --gray-angle DEG

arrange dots by `DEG` degrees in Gray channel

#### -t DEG DEG DEG, --Angles DEG DEG DEG, --rgb-angles DEG DEG DEG

arrange dots by `DEG` degrees in each RGB channels

#### -a DEG DEG DEG DEG, --angles DEG DEG DEG DEG, --cmyk-angles DEG DEG DEG DEG

arrange dots by `DEG` degrees in each CMYK channels

#### -m {auto,gray,rgb,cmyk}, --mode {auto,gray,rgb,cmyk}

color space type to generate halftones

The default is `auto`.
It means that Gray images will be Gray halftones, and colored images will be CMYK halftones.

#### -o {auto,gray,rgb,cmyk}, --output {auto,gray,rgb,cmyk}

color space type to save output images

The default is `auto`.
It means that Gray images will be saved as Gray images, and colored images will be saved as RGB images.

#### -T, --tiff, --out-tiff

save TIFF images instead of PNG images

CMYK images will always be saved in TIFF regardless of this option.

#### -G GRAY_ICC_FILE, --input-gray-profile GRAY_ICC_FILE

specify ICC profile for input Gray images

#### -I RGB_ICC_FILE, --input-rgb-profile RGB_ICC_FILE

specify ICC profile for input RGB images

#### -M CMYK_ICC_FILE, --input-cmyk-profile CMYK_ICC_FILE

specify ICC profile for input CMYK images

#### -L GRAY_ICC_FILE, --gray-profile GRAY_ICC_FILE

specify ICC profile for transform to Gray images

#### -l {per,sat,rel,abs,0,1,2,3}, --gray-intent {per,sat,rel,abs,0,1,2,3}

rendering intent for transform to Gray images

#### -R RGB_ICC_FILE, --rgb-profile RGB_ICC_FILE

specify ICC profile for transform to RGB images

#### -r {per,sat,rel,abs,0,1,2,3}, --rgb-intent {per,sat,rel,abs,0,1,2,3}

rendering intent for transform to RGB images

#### -C CMYK_ICC_FILE, --cmyk-profile CMYK_ICC_FILE

specify ICC profile for transform to CMYK images

#### -c {per,sat,rel,abs,0,1,2,3}, --cmyk-intent {per,sat,rel,abs,0,1,2,3}

rendering intent for transform to CMYK images

#### -H, --allow-huge

disable the limitation of input image size

Be careful.
This option may make DoS attacks possible.

#### --ignore, --ignore-embedded-profile

don't use ICC profiles embedded in input images

#### --discard, --discard-profile

don't embed ICC profiles in output images

#### --naive, --naive-transform

use approximate conversion algorithm (naive transform) instead of ICC-based transform

#### --gamma-correction

apply gamma correction of sRGB for RGB-CMYK conversion when the naive transform is used

#### --key RATE, --key-from RATE

black ingredient threshold within 0.0-1.0 for RGB-CMYK conversion when the naive transform is used

#### -K, --keep-all

don't convert any channels to halftones

This is useful for looking color space transform.

#### --keep-red

don't convert R channels to halftones

#### --keep-green

don't convert G channels to halftones

#### --keep-blue

don't convert B channels to halftones

#### --keep-cyan

don't convert C channels to halftones

#### --keep-magenta

don't convert M channels to halftones

#### --keep-yellow

don't convert Y channels to halftones

#### --keep-key

don't convert K channels to halftones

## Gallery

### RGB

![Blue Hyacinths](images/blue-hyacinths.png)

### CMYK

![Todai Ramen](images/lighthouse-ramen.png)

### Gray

![Chevrolet Opala 87](images/chevrolet-opala.png)

## Credits

This application contains some ICC profiles to convert images between different color spaces.
[sGray.icc](profiles/sGray.icc), [sRGB.icc](profiles/sRGB.icc) and [SWOP.icc](profiles/SWOP.icc) are provided by Artifex Software as a part of [GPL Ghostscript](https://www.ghostscript.com/) under the [GNU Affero General Public License v3.0](https://www.gnu.org/licenses/agpl-3.0.html).

## License

[GNU Affero General Public License v3.0](LICENSE)
