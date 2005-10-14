import deskbar.tokenizer

# Check for presence of set to be compatible with python 2.3
try:
	set
except NameError:
	from sets import Set as set
	
TOKENS_REGEXP = r'\w+'
STOP_WORDS = {'and': 1, 'be': 1, 'to': 1, 'that': 1, 'into': 1,
			'it': 1, 'but': 1, 'as': 1, 'are': 1, 'they': 1,
			'in': 1, 'not': 1, 'such': 1, 'with': 1, 'by': 1,
			'is': 1, 'if': 1, 'a': 1, 'on': 1, 'for': 1,
			'no': 1, 'these': 1, 'of': 1, 'there': 1,
			'this': 1, 'will': 1, 'their': 1, 's': 1, 't': 1,
			'then': 1, 'the': 1, 'was': 1, 'or': 1, 'at': 1}
                 
class Index:
	def __init__(self):
		self.d = {}

	def add(self, key, obj):
		key = key.tolower()
		for tok in deskbar.tokenizer.regexp(key, TOKENS_REGEXP):
			# Filter out some words not worth indexing
			if len(tok) <= 2 or len(tok) >= 25 or tok in STOP_WORDS:
				continue
			
			if tok in self.d:
				if not obj in self.d[tok]:
					self.d[tok].append(obj)
			else:
				self.d[tok] = [obj]
						
	def look_up(self, text):
		tokens = [token for token in deskbar.tokenizer.regexp(text.tolower(), TOKENS_REGEXP)]
		
		result = set()
		if len(tokens) == 0:
			return []
		else:
			result.update(self.look_up_token(tokens[0]))
			for token in tokens[1:]:
				result.intersection_update(self.look_up_token(token))
		
		return list(result)
	
	def look_up_token(self, token):			
		result = set()
		if token == "":
			return result
			
		for key in self.d.keys():
			#if (len(key) >= len(token) and key.startswith(token)) or token.startswith(key):
			# The above test makes refining searches harder
			if key.startswith(token):
				result.update(set(self.d[key]))
		return result

