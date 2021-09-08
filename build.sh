#!/bin/sh

set -e

# Download source

mkdir -p fonts
wget -nc -P fonts https://github.com/ButTaiwan/genyo-font/releases/download/v1.501/GenYoMin.zip
unzip -n fonts/GenYoMin.zip "*.ttc" -d fonts

# Generate fonts

font_version=1.007

mkdir -p output

for input_file in fonts/*.ttc; do
    output_file=$(echo $input_file | sed -e 's#fonts/GenYoMin-\(.*\).ttc#output/FanWunMing-\1.ttf#g')
    output_file_twp=$(echo $input_file | sed -e 's#fonts/GenYoMin-\(.*\).ttc#output/FanWunMing-TW-\1.ttf#g')

    # no-twp
    python -m OpenCCFontGenerator \
        -i $input_file \
        -o $output_file \
        -n config/name.json \
        --ttc-index=0 \
        --font-version=$font_version

    # twp
    python -m OpenCCFontGenerator \
        -i $input_file \
        -o $output_file_twp \
        -n config/name-twp.json \
        --ttc-index=0 \
        --font-version=$font_version \
        --twp
done
