# Build convert tables
#
# Input:
# - build/t2twp.json
#    -> opencc_data/TWPhrases.txt
#    -> opencc_data/TWVariants.txt
# - opencc_data/STCharacters.txt
# - opencc_data/STPhrases.txt
# - opencc_data/TWVariants.txt
# - opencc_data/TWPhrases.txt
#
# Output:
# - cache/convert_table_words.txt
# - cache/convert_table_chars.txt
# - cache/convert_table_words_twp.txt
# - cache/convert_table_chars_twp.txt

from opencc import OpenCC

def build_entries(twp=False):
	with open('opencc_data/STCharacters.txt') as f:  # s2t
		for line in f:
			k, vx = line.rstrip('\n').split('\t')
			v = vx.split(' ')[0]  # Only select the first candidate
			v = t2twp(v) if twp else v  # s2t -> s2twp
			yield k, v

	with open('opencc_data/STPhrases.txt') as f:  # s2t
		for line in f:
			k, vx = line.rstrip('\n').split('\t')
			v = vx.split(' ')[0]  # Only select the first candidate
			v = t2twp(v) if twp else v  # s2t -> s2twp
			yield k, v

	if twp:
		with open('opencc_data/TWVariants.txt') as f:  # t2tw
			for line in f:
				k, vx = line.rstrip('\n').split('\t')
				v = vx.split(' ')[0]  # Only select the first candidate
				k = t2s(k)  # t2tw -> s2tw
				yield k, v

		with open('opencc_data/TWPhrases.txt') as f:  # t2twp
			for line in f:
				k, vx = line.rstrip('\n').split('\t')
				v = vx.split(' ')[0]  # Only select the first candidate
				k = t2s(k)  # t2twp -> s2twp
				yield k, v

def go(twp=False):
	entries = build_entries(twp=twp)
	entries = dict(entries)  # remove duplicates
	entries = sorted(entries.items(), key=lambda k_v: (len(k_v[0]), k_v[0]), reverse=True)  # sort

	twp_suffix = '_twp' if twp else ''

	with open(f'cache/convert_table_words{twp_suffix}.txt', 'w') as f1, \
	open(f'cache/convert_table_chars{twp_suffix}.txt', 'w') as f2:
		for k, v in entries:
			print(k, v, sep='\t', file=f1 if len(k) > 1 else f2)

if __name__ == '__main__':
	# Initialize OpenCC converters
	t2s = OpenCC('t2s').convert
	t2twp = OpenCC('./build/t2twp').convert

	go()
	go(twp=True)
