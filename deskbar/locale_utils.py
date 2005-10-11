from os import getenv
import re

COMPONENT_CODESET   = 1
COMPONENT_TERRITORY = 2
COMPONENT_MODIFIER  = 4
  
def get_locale(category):
	# The highest priority value is the `LANGUAGE' environment
	# variable.  This is a GNU extension.
	retval = getenv ("LANGUAGE")
	if retval != None and retval != "":
		return retval

	# `LANGUAGE' is not set.  So we have to proceed with the POSIX
	# methods of looking to `LC_ALL', `LC_xxx', and `LANG'.  On some
	# systems this can be done by the `setlocale' function itself.

	# Setting of LC_ALL overwrites all other.
	retval = getenv ("LC_ALL")
	if retval != None and retval != "":
		return retval

	# Next comes the name of the desired category.
	retval = getenv (category)
	if retval != None and retval != "":
		return retval

	# Last possibility is the LANG environment variable.
	retval = getenv ("LANG")
	if retval != None and retval != "":
		return retval

	return None

def get_languages():
	value = get_locale("LC_MESSAGES")
	if value == None:
		value = "C"

	languages = []
	values = value.split(":")
	for lang in values:
		# FIXME: we are forgetting the /usr/share/locale/locale.alias file.
		# See: gutils.c:2482: static char * unalias_lang (char *lang)
		# lang = unalias_lang(lang)
		for variant in compute_locale_variants(lang):
			languages.append(variant)
	
	languages.append("C")
	return languages

def compute_locale_variants (locale):
	mask, language, territory, codeset, modifier = explode_locale (locale)
	
	variants = []
	# Iterate through all possible combinations, from least attractive
	# to most attractive.
	for i in range(mask+1):
		if (i & ~mask) == 0:
			val = language
			if i & COMPONENT_TERRITORY:
				val = val+territory
			if i & COMPONENT_CODESET:
				val = val+codeset
			if i & COMPONENT_MODIFIER:
				val = val+modifier
			
			variants.append(val)

	return variants

LANG = re.compile(r'([a-zA-Z0-9]+)(_[a-zA-Z0-9]+)?(\.[a-zA-Z0-9]+)?(@[a-zA-Z0-9]+)?')
def explode_locale (locale):
	mask = 0
	territory = codeset = modifier = ""
	
	match = LANG.match(locale)
	if match == None:
		return locale
	
	language = match.group(1)
	
	if match.group(2) != None:
		mask = mask | COMPONENT_TERRITORY
		territory = match.group(2)
		
	if match.group(3) != None:
		mask = mask | COMPONENT_CODESET
		codeset = match.group(3)
		
	if match.group(4) != None:
		mask = mask | COMPONENT_MODIFIER
		modifier = match.group(4)

	return mask, language, territory, codeset, modifier
