import portstem, tokenizer

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
		self.stemmer = portstem.PorterStemmer()

	def add(self, key, obj):
		for tok in tokenizer.regexp(key, TOKENS_REGEXP):
			# Filter out some words not worth indexing
			if len(tok) <= 2 or len(tok) >= 25 or tok in STOP_WORDS:
				continue
			stemmed = self.stemmer.stem(tok)
			
			if stemmed in self.d:
				if not obj in self.d[stemmed]:
					self.d[stemmed].append(obj)
			else:
				self.d[stemmed] = [obj]
			#print 'Indexed words:', self.d.keys()
						
	def look_up(self, text):
		tokens = [self.stemmer.stem(token) for token in tokenizer.regexp(text, TOKENS_REGEXP)]
		
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
		for key in self.d.keys():
			if (len(key) >= len(token) and key.startswith(token)) or token.startswith(key):
				result.update(set(self.d[key]))
		return result

