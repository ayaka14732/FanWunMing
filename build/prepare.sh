#!/bin/sh
mkdir -p output
wget -q -nc -P cache https://github.com/ButTaiwan/genyo-font/releases/download/v1.501/GenYoMin.zip
wget -q -nc -P cache https://cdn.jsdelivr.net/npm/opencc-data@1.0.4/data/STCharacters.txt
wget -q -nc -P cache https://cdn.jsdelivr.net/npm/opencc-data@1.0.4/data/STPhrases.txt
wget -q -nc -P cache https://cdn.jsdelivr.net/npm/opencc-data@1.0.4/data/TWPhrasesIT.txt
wget -q -nc -P cache https://cdn.jsdelivr.net/npm/opencc-data@1.0.4/data/TWPhrasesName.txt
wget -q -nc -P cache https://cdn.jsdelivr.net/npm/opencc-data@1.0.4/data/TWPhrasesOther.txt
wget -q -nc -P cache https://cdn.jsdelivr.net/npm/opencc-data@1.0.4/data/TWVariants.txt
cat cache/TWPhrasesIT.txt cache/TWPhrasesName.txt cache/TWPhrasesOther.txt > cache/TWPhrases.txt
wget -q -nc -P cache https://gist.githubusercontent.com/fatum12/941a10f31ac1ad48ccbc/raw/59d7e29b307ae3439317a975ef390cd729f9bc17/ttc2ttf.pe
wget -q -nc -P cache https://raw.githubusercontent.com/rime-aca/character_set/e7d009a8a185a83f62ad2c903565b8bb85719221/通用規範漢字表.txt
unzip -q -n -d cache cache/GenYoMin.zip "*.ttc"
