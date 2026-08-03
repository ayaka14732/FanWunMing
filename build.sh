#!/bin/sh

set -eu

source_version=2.100
font_version=2.100
archive=fonts/GenYoMin2-ttc.zip
archive_checksum=292b3af4232d070483e2fa6f09b56a328a4d47da04b4e9d354a6d6d15f2c1f73

# Download source

mkdir -p fonts
if [ ! -f "$archive" ]; then
    curl --fail --location --retry 3 --output "$archive" "https://github.com/ButTaiwan/genyo-font/releases/download/v$source_version/GenYoMin2-ttc.zip"
fi
actual_checksum=$(shasum -a 256 "$archive" | cut -d ' ' -f 1)
if [ "$actual_checksum" != "$archive_checksum" ]; then
    echo "Checksum mismatch for $archive" >&2
    exit 1
fi
unzip -o "$archive" '*.ttc' -d fonts

# Generate fonts

mkdir -p output
for input_file in fonts/GenYoMin2-*.ttc; do
    style=${input_file#fonts/GenYoMin2-}
    style=${style%.ttc}
    output_file="output/FanWunMing-$style.ttf"
    output_file_twp="output/FanWunMing-TW-$style.ttf"

    python3 -m OpenCCFontGenerator -i "$input_file" -o "$output_file" -n config/name.json --ttc-index 0 --font-version "$font_version"
    python3 -m OpenCCFontGenerator -i "$input_file" -o "$output_file_twp" -n config/name-twp.json --ttc-index 0 --font-version "$font_version" --twp
done
