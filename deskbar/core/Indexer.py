"""
A simple indexer which splits tokens in a string
"""

# Check for presence of set to be compatible with python 2.3
try:
    set
except NameError:
    from sets import Set as set

STOP_WORDS = {'and': 1, 'that': 1, 'into': 1,
            'but': 1, 'are': 1, 'they': 1,
            'not': 1, 'such': 1, 'with': 1,
            'for': 1, 'these': 1, 'there': 1,
            'this': 1, 'will': 1, 'their': 1,
            'then': 1, 'the': 1, 'was': 1}
                 
class Indexer:
    def __init__(self):
        self.d = {}

    def add(self, key, obj):
        key = key.lower()
        for tok in key.split():
            # Filter out some words not worth indexing
            if len(tok) <= 2 or len(tok) >= 25 or tok in STOP_WORDS:
                continue
            
            if tok in self.d:
                if not obj in self.d[tok]:
                    self.d[tok].append(obj)
            else:
                self.d[tok] = [obj]
                        
    def look_up(self, text):
        tokens = [token for token in text.lower().split() if len(token) > 2 and len(token) < 25 and token not in STOP_WORDS]
        
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
            if key.startswith(token):
                result.update(set(self.d[key]))
        return result

