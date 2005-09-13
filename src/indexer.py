import shlex


class Index:
	def __init__(self):
		self.d = {}


	def clear(self):
		self.d.clear()


	def add(self, key, obj):
		lexer = shlex.shlex(str(key).lower())
		lexer.whitespace = lexer.whitespace + ",.<>!@#$%^&*()[]{}-_=+\\|`~'\"/?;:"
		tokens = set()
		while True:
			token = lexer.get_token()
			if not token:
				break
			tokens.add(token)
		for t in tokens:
			if self.d.has_key(t):
				self.d[t].append(obj)
			else:
				self.d[t] = [obj]


	def look_up(self, text):
		if len(text) == 0:
			return []
		
		tokens = text.lower().split()
		
		if len(tokens) == 1:
			return list(self.look_up_single_token(tokens[0]))
		elif len(tokens) == 0:
			return []
		else:
			result = self.look_up_single_token(tokens[0])
			for t in tokens[1:]:
				hits = self.look_up_single_token(t)
				result = result.intersection(hits)
			return list(result)


	def look_up_single_token(self, token):
		result = set()
		for k in self.d.keys():
			if k.startswith(token):
				result.update(set(self.d[k]))
		return result
