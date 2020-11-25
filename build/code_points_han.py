# Code points of Han characters to be included:
# 1. Code points in Tongyong Guifan Hanzi Biao (通用规范汉字表)
# 2. Code points in OpenCC dictionaries

from itertools import chain

s = set()

with open('cache/通用規範漢字表.txt') as f:
	for line in f:
		if line and not line.startswith('#'):
			c = line[0]
			s.add(ord(c))

with open('opencc_data/STCharacters.txt') as f1, \
open('opencc_data/STPhrases.txt') as f2, \
open('opencc_data/TWVariants.txt') as f3, \
open('opencc_data/TWPhrases.txt') as f4, \
open('opencc_data/HKVariants.txt') as f5:
	for line in chain(f1, f2, f3, f4, f5):
		k, vx = line.rstrip('\n').split('\t')
		vs = vx.split(' ')
		for c in k:
			s.add(ord(c))
		for v in vs:
			for c in v:
				s.add(ord(c))

for c in '妳':
	s.add(ord(c))

with open('cache/code_points_han.txt', 'w') as f:
	for cp in sorted(s):
		if cp > 128:  # remove letters in the dictionaries
			print(cp, file=f)
