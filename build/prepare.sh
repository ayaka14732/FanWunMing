#!/bin/sh
mkdir -p cache output
cd cache
curl -LsSO https://github.com/ButTaiwan/genyo-font/releases/download/v1.501/GenYoMin.zip
curl -LsSZ --remote-name-all https://cdn.jsdelivr.net/npm/opencc-data@1.0.5/data/{STCharacters.txt,STPhrases.txt,TWPhrasesIT.txt,TWPhrasesName.txt,TWPhrasesOther.txt,TWVariants.txt}
curl -LsSo 通用規範漢字表.txt https://raw.githubusercontent.com/rime-aca/character_set/e7d009a8a185a83f62ad2c903565b8bb85719221/%E9%80%9A%E7%94%A8%E8%A6%8F%E7%AF%84%E6%BC%A2%E5%AD%97%E8%A1%A8.txt
cat TWPhrasesIT.txt TWPhrasesName.txt TWPhrasesOther.txt > TWPhrases.txt
unzip -q -n GenYoMin.zip "*.ttc"
