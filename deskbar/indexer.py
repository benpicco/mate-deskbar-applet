import portstem, tokenizer

TOKENS_REGEXP = r'\w+'
class Index:
	def __init__(self):
		self.d = {}
		self.stemmer = portstem.PorterStemmer()

	def add(self, key, obj):
		for tok in tokenizer.regexp(key, TOKENS_REGEXP):
			stemmed = self.stemmer.stem(tok)
			
			if tok in self.d:
				if not obj in self.d[tok]:
					self.d[tok].append(obj)
			else:
				self.d[tok] = [obj]
						
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
			if key.startswith(token):
				result.update(set(self.d[key]))
				
		return result

