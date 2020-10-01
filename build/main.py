from collections import defaultdict
from datetime import date
from glob import glob
from itertools import chain
import json
from opencc import OpenCC
import os
import subprocess

FONT_VERSION = 1.003

# Define the max entries size in a subtable.
# We define a number that is small enough here, so that the entries will not exceed
# the size limit.
SUBTABLE_MAX_COUNT = 4000

# This function is used to split a GSUB table into several subtables.
def grouper(lst, n, start=0):
	'''
	Split a list into chunks of size n.
	>>> list(grouper([1, 2, 3, 4, 5], 2))
	[[1, 2], [3, 4], [5]]
	'''
	while start < len(lst):
		yield lst[start:start+n]
		start += n

# An opentype font can hold at most 65535 glyphs.
MAX_GLYPH_COUNT = 65535

# Here we are going to add a special key, cmap_rev, to the font object.
# This key is the reverse mapping of the cmap table and will be used in next steps.
def build_cmap_rev(obj):
	cmap_rev = defaultdict(list)
	for codepoint, glyph_name in obj['cmap'].items():
		cmap_rev[glyph_name].append(codepoint)
	return cmap_rev

def load_font(path, ttc_index=None):
	'''Load a font as a JSON object.'''
	ttc_index_args = () if ttc_index is None else ('--ttc-index', str(ttc_index))
	obj = json.loads(subprocess.check_output(('otfccdump', path, *ttc_index_args)))
	obj['cmap_rev'] = build_cmap_rev(obj)
	return obj

def save_font(obj, path):
	'''Save a font object to file.'''
	del obj['cmap_rev']
	subprocess.run(('otfccbuild', '-o', path), input=json.dumps(obj), encoding='utf-8')

def codepoint_to_glyph_name(obj, codepoint):
	'''Convert a codepoint to a glyph name in a font.'''
	return obj['cmap'][str(codepoint)]

def insert_empty_glyph(obj, name):
	'''Insert an empty glyph to a font with the given name.'''
	obj['glyf'][name] = {'advanceWidth': 0, 'advanceHeight': 1000, 'verticalOrigin': 880}
	obj['glyph_order'].append(name)

def get_glyph_count(obj):
	'''Get the total numbers of glyph in a font.'''
	return len(obj['glyph_order'])

def build_codepoints_tonggui():
	'''Build a set of all the codepoints in Tongyong Guifan Hanzi Biao (通用规范汉字表).'''
	with open('cache/通用規範漢字表.txt') as f:
		return {ord(line[0]) for line in f if line and not line.startswith('#')}

def build_codepoints_font(obj):
	'''Build a set of all the codepoints in a font.'''
	return set(map(int, obj['cmap']))

def build_codepoints_non_han():
	'''Build a set of codepoints of the needed non-Han characters in the final font.'''
	return set(chain(
		range(0x0020, 0x007E + 1),
		range(0x02B0, 0x02FF + 1),
		range(0x2002, 0x203B + 1),
		range(0x2E00, 0x2E7F + 1),
		range(0x2E80, 0x2EFF + 1),
		range(0x3000, 0x301C + 1),
		range(0x3100, 0x312F + 1),
		range(0x3190, 0x31BF + 1),
		range(0xFE10, 0xFE1F + 1),
		range(0xFE30, 0xFE4F + 1),
		range(0xFF01, 0xFF5E + 1),
		range(0xFF5F, 0xFF60 + 1),
		range(0xFF61, 0xFF64 + 1),
	))

# We restrict the Simplified Chinese characters (on the left side of the OpenCC dictionary
# file) to the range of Tongyong Guifan Hanzi Biao, and discard those conversions that are
# out of range. The remained conversions are stored in the entries variable.
#
# Then we calculate the range of “Which Traditional Chinese characters are needed if we
# convert Tongyong Guifan Hanzi Biao to Traditional Chinese”. The range is stored in the
# codepoints variable.
def build_opencc_char_table(codepoints_tonggui, codepoints_font, twp=False):
	entries = []
	codepoints = set()

	with open('cache/STCharacters.txt') as f:  # s2t
		for line in f:
			k, vx = line.rstrip('\n').split('\t')
			v = vx.split(' ')[0]  # Only select the first candidate
			v = t2twp(v) if twp else v  # s2t -> s2twp
			codepoint_k = ord(k)
			codepoint_v = ord(v)
			if codepoint_k in codepoints_tonggui and codepoint_v in codepoints_font:
				entries.append((codepoint_k, codepoint_v))
				codepoints.add(codepoint_v)

	return entries, codepoints

def build_opencc_word_table(codepoints_tonggui, codepoints_font, twp=False):
	entries = {}
	codepoints = set()

	with open('cache/STPhrases.txt') as f:  # s2t
		for line in f:
			k, vx = line.rstrip('\n').split('\t')
			v = vx.split(' ')[0]  # Only select the first candidate
			v = t2twp(v) if twp else v  # s2t -> s2twp
			codepoints_k = tuple(ord(c) for c in k)
			codepoints_v = tuple(ord(c) for c in v)
			if all(codepoint in codepoints_tonggui for codepoint in codepoints_k) \
			and all(codepoint in codepoints_font for codepoint in codepoints_v):
				entries[codepoints_k] = codepoints_v
				codepoints.update(codepoints_v)

	if twp:
		with open('cache/TWPhrases.txt') as f:  # t2twp
			for line in f:
				k, vx = line.rstrip('\n').split('\t')
				v = vx.split(' ')[0]  # Only select the first candidate
				k = t2s(k)  # t2twp -> s2twp
				codepoints_k = tuple(ord(c) for c in k)
				codepoints_v = tuple(ord(c) for c in v)
				if all(codepoint in codepoints_tonggui for codepoint in codepoints_k) \
				and all(codepoint in codepoints_font for codepoint in codepoints_v):
					entries[codepoints_k] = codepoints_v
					codepoints.update(codepoints_v)

	# Sort from longest to shortest to force longest match
	return sorted(((k, v) for k, v in entries.items()), key=lambda k_v: (-len(k_v[0]), k_v[0])), codepoints

def disassociate_codepoint_and_glyph_name(obj, codepoint, glyph_name):
	'''
	Remove a codepoint from the cmap table of a font object.

	Returns `True` if the codepoint is the only codepoint that is associated
	with the glyph. Otherwise returns `False`.
	'''
	# Remove glyph from cmap table
	del obj['cmap'][codepoint]

	is_only_item = obj['cmap_rev'][glyph_name] == [codepoint]

	# Remove glyph from cmap_rev
	if is_only_item:
		del obj['cmap_rev'][glyph_name]
	else:
		obj['cmap_rev'][glyph_name].remove(codepoint)

	return is_only_item

def remove_codepoint(obj, codepoint):
	'''Remove a codepoint from a font object.'''
	codepoint = str(codepoint)

	glyph_name = obj['cmap'].get(codepoint)
	if not glyph_name:
		return  # The codepoint is not associated with a glyph name. No action is needed

	is_only_item = disassociate_codepoint_and_glyph_name(obj, codepoint, glyph_name)
	if is_only_item:
		remove_glyph(obj, glyph_name)

def remove_codepoints(obj, codepoints):
	'''Remove a sequence of codepoints from a font object.'''
	for codepoint in codepoints:
		remove_codepoint(obj, codepoint)

def remove_associated_codepoints_of_glyph(obj, glyph_name):
	'''Remove a glyph from the cmap table of a font object.'''
	# Remove glyph from cmap table
	for codepoint in obj['cmap_rev'][glyph_name]:
		del obj['cmap'][codepoint]

	# Remove glyph from cmap_rev
	del obj['cmap_rev'][glyph_name]

def remove_glyph(obj, glyph_name):
	'''Remove a glyph from all the tables except the cmap table of a font object.'''
	# Remove glyph from glyph_order table
	try:
		obj['glyph_order'].remove(glyph_name)
	except ValueError as e:
		pass

	# Remove glyph from glyf table
	del obj['glyf'][glyph_name]

	# Remove glyph from GSUB table
	for lookup in obj['GSUB']['lookups'].values():
		if lookup['type'] == 'gsub_single':  # {a: b}
			for subtable in lookup['subtables']:
				for k, v in list(subtable.items()):
					if glyph_name == k or glyph_name == v:
						del subtable[k]
		elif lookup['type'] == 'gsub_alternate':  # {a: [b1, b2, ...]}
			for subtable in lookup['subtables']:
				for k, v in list(subtable.items()):
					if glyph_name == k or glyph_name in v:
						del subtable[k]
		elif lookup['type'] == 'gsub_ligature':  # {from: [a1, a2, ...], to: b}
			for subtable in lookup['subtables']:
				predicate = lambda item: glyph_name not in item['from'] and glyph_name != item['to']
				subtable['substitutions'][:] = filter(predicate, subtable['substitutions'])
		else:
			raise NotImplementedError('Unknown GSUB lookup type')

	# Remove glyph from GPOS table
	for lookup in obj['GPOS']['lookups'].values():
		if lookup['type'] == 'gpos_single':  # {a: ...}
			for subtable in lookup['subtables']:
				subtable.pop(glyph_name, None)
		elif lookup['type'] == 'gpos_pair':  # {first: {a1: ..., a2: ...}, second: {b1: ..., b2: ...}, ...}
			for subtable in lookup['subtables']:
				subtable['first'].pop(glyph_name, None)
				subtable['second'].pop(glyph_name, None)
		else:
			raise NotImplementedError('Unknown GPOS lookup type')

def get_reachable_glyphs(obj):
	'''Get all the reachable glyphs of a font object.'''
	reachable_glyphs = {'.notdef', '.null'}

	for glyph_name in obj['cmap'].values():
		# Add the glyph in cmap table
		reachable_glyphs.add(glyph_name)

		# Add the glyphs referenced by the glyph in cmap table
		for lookup in obj['GSUB']['lookups'].values():
			if lookup['type'] == 'gsub_single':  # {a: b}
				for subtable in lookup['subtables']:
					for k, v in subtable.items():
						if glyph_name == k:
							reachable_glyphs.add(v)
			elif lookup['type'] == 'gsub_alternate':  # {a: [b1, b2, ...]}
				for subtable in lookup['subtables']:
					for k, vs in subtable.items():
						if glyph_name == k:
							reachable_glyphs.update(vs)
			elif lookup['type'] == 'gsub_ligature':  # {from: [a1, a2, ...], to: b}
				for subtable in lookup['subtables']:
					for item in subtable['substitutions']:
						if glyph_name in item['from']:
							reachable_glyphs.add(item['to'])
			else:
				raise NotImplementedError('Unknown GSUB lookup type')

	return reachable_glyphs

def clean_unused_glyphs(obj):
	reachable_glyphs = get_reachable_glyphs(obj)
	all_glyphs = set(obj['glyph_order'])
	for glyph_name in all_glyphs - reachable_glyphs:
		remove_associated_codepoints_of_glyph(obj, glyph_name)
		remove_glyph(obj, glyph_name)

def insert_empty_feature(obj, feature_name):
	for table in obj['GSUB']['languages'].values():
		table['features'].append(feature_name)
	obj['GSUB']['features'][feature_name] = []

def create_word2pseu_table(obj, feature_name, conversions):
	obj['GSUB']['features'][feature_name].append('word2pseu')
	obj['GSUB']['lookups']['word2pseu'] = {
		'type': 'gsub_ligature',
		'flags': {},
		'subtables': [{'substitutions': subtable} for subtable in grouper(conversions, SUBTABLE_MAX_COUNT)]
	}
	obj['GSUB']['lookupOrder'].append('word2pseu')

def create_char2char_table(obj, feature_name, conversions):
	obj['GSUB']['features'][feature_name].append('char2char')
	obj['GSUB']['lookups']['char2char'] = {
		'type': 'gsub_single',
		'flags': {},
		'subtables': [{k: v for k, v in subtable} for subtable in grouper(conversions, SUBTABLE_MAX_COUNT)]
	}
	obj['GSUB']['lookupOrder'].append('char2char')

def create_pseu2word_table(obj, feature_name, conversions):
	obj['GSUB']['features'][feature_name].append('pseu2word')
	obj['GSUB']['lookups']['pseu2word'] = {
		'type': 'gsub_multiple',
		'flags': {},
		'subtables': [{k: v for k, v in subtable} for subtable in grouper(conversions, SUBTABLE_MAX_COUNT)]
	}
	obj['GSUB']['lookupOrder'].append('pseu2word')

def build_fanwunming_name_header(style, version, date, twp=False):
	with open('build/name.json') as f:
		name_header = json.load(f)

	for item in name_header:
		item['nameString'] = item['nameString'] \
		.replace('<Style>', style) \
		.replace('<Version>', version) \
		.replace('<Date>', date)

		if twp:
			item['nameString'] = item['nameString'] \
			.replace('繁媛明朝', '繁媛明朝 TW') \
			.replace('Fan Wun Ming', 'Fan Wun Ming TW') \
			.replace('FanWunMing', 'FanWunMing-TW')

	return name_header

def modify_metadata(obj, twp=False):
	style = next(item['nameString'] for item in obj['name'] if item['nameID'] == 17)
	today = date.today().strftime('%b %d, %Y')

	name_header = build_fanwunming_name_header(style, str(FONT_VERSION), today, twp=twp)

	obj['head']['fontRevision'] = FONT_VERSION
	obj['name'] = name_header

def build_dest_path_from_src_path(path, twp=False):
	'''
	>>> build_dest_path_from_src_path('cache/GenYoMin-R.ttc')
	'output/FanWunMing-R.ttf'
	'''
	return path \
	.replace('cache/', 'output/') \
	.replace('GenYoMin', 'FanWunMing' + ('-TW' if twp else '')) \
	.replace('ttc', 'ttf')

def go(path, twp=False):
	font = load_font(path, ttc_index=0)

	codepoints_font = build_codepoints_font(font)
	codepoints_tonggui = build_codepoints_tonggui() & codepoints_font

	codepoints_final = codepoints_tonggui | build_codepoints_non_han() & codepoints_font

	entries_char, codepoints_char = build_opencc_char_table(codepoints_tonggui, codepoints_font, twp=twp)
	codepoints_final |= codepoints_char

	entries_word, codepoints_word = build_opencc_word_table(codepoints_tonggui, codepoints_font, twp=twp)
	codepoints_final |= codepoints_word

	remove_codepoints(font, codepoints_font - codepoints_final)
	clean_unused_glyphs(font)

	available_glyph_count = MAX_GLYPH_COUNT - get_glyph_count(font)
	assert available_glyph_count >= len(entries_word)

	word2pseu_table = []
	char2char_table = []
	pseu2word_table = []

	for i, (codepoints_k, codepoints_v) in enumerate(entries_word):
		pseudo_glyph_name = 'pseu%X' % i
		glyph_names_k = [codepoint_to_glyph_name(font, codepoint) for codepoint in codepoints_k]
		glyph_names_v = [codepoint_to_glyph_name(font, codepoint) for codepoint in codepoints_v]
		insert_empty_glyph(font, pseudo_glyph_name)
		word2pseu_table.append({'from': glyph_names_k, 'to': pseudo_glyph_name})
		pseu2word_table.append((pseudo_glyph_name, glyph_names_v))

	for codepoint_k, codepoint_v in entries_char:
		glyph_name_k = codepoint_to_glyph_name(font, codepoint_k)
		glyph_name_v = codepoint_to_glyph_name(font, codepoint_v)
		char2char_table.append((glyph_name_k, glyph_name_v))

	feature_name = 'liga_s2t'
	insert_empty_feature(font, feature_name)
	create_word2pseu_table(font, feature_name, word2pseu_table)
	create_char2char_table(font, feature_name, char2char_table)
	create_pseu2word_table(font, feature_name, pseu2word_table)

	modify_metadata(font, twp=twp)
	save_font(font, build_dest_path_from_src_path(path, twp=twp))

if __name__ == '__main__':
	# Initialize OpenCC converters
	t2s = OpenCC('t2s').convert
	t2twp = OpenCC('./build/t2twp').convert

	for path in glob('cache/GenYoMin-*.ttc'):
		go(path)
		go(path, twp=True)
