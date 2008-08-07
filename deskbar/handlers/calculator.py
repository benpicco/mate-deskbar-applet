#
#  calculator.py : A calculator module for the deskbar applet.
#
#  Copyright (C) 2008 by Johannes Buchner
#  Copyright (C) 2007 by Michael Hofmann
#  Copyright (C) 2006 by Callum McKenzie
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
# 
#  Authors: 
#      Callum McKenzie <callum@spooky-possum.org> - Original author
#      Michael Hofmann <mh21@piware.de> - compatibility changes for deskbar 2.20
#      Johannes Buchner <buchner.johannes@gmx.at> - Made externally usable
#
#  This version of calculator can be used with converter
#    read how at http://twoday.tuwien.ac.at/jo/search?q=calculator+converter+deskbar
#

from __future__ import division
from deskbar.handlers.actions.CopyToClipboardAction import CopyToClipboardAction
from deskbar.defs import VERSION
from gettext import gettext as _
import deskbar.core.Utils
import deskbar.interfaces.Match
import deskbar.interfaces.Module
import logging
import math
import re

LOGGER = logging.getLogger(__name__)

HANDLERS = ["CalculatorModule"]

def bin (n):
    """A local binary equivalent of the hex and oct builtins."""
    if (n == 0):
        return "0b0"
    s = ""
    if (n < 0):
        while n != -1:
            s = str (n & 1) + s
            n >>= 1
        return "0b" + "...111" + s            
    else:
        while n != 0:
            s = str (n & 1) + s
            n >>= 1
        return "0b" + s

# These next three make sure {hex, oct, bin} can handle floating point,
# by rounding. This makes sure things like hex(255/2) behave as a
# programmer would expect while allowing 255/2 to equal 127.5 for normal
# people. Abstracting out the body of these into a single function which
# takes hex, oct or bin as an argument seems to run into problems with
# those functions not being defined correctly in the resticted eval (?).

def lenient_hex (c):
    try:
        return hex (c)
    except TypeError:
        return hex (int (c))

def lenient_oct (c):
    try:
        return oct (c)
    except TypeError:
        return oct (int (c))

def lenient_bin (c):
    try:
        return bin (c)
    except TypeError:
        return bin (int (c))

class CalculatorAction (CopyToClipboardAction):

    def __init__ (self, text, answer):
        CopyToClipboardAction.__init__ (self, answer, answer)
        self.text = text

    def get_verb(self):
        return _("Copy <b>%(origtext)s = %(name)s</b> to clipboard")

    def get_name(self, text = None):
        """Because the text variable for history entries contains the text
        typed for the history search (and not the text of the orginal action),
        we store the original text seperately."""
        result = CopyToClipboardAction.get_name (self, text)
        result["origtext"] = self.text
        return result

    def get_tooltip(self, text=None):
        return self._name
      
class CalculatorMatch (deskbar.interfaces.Match):

    def __init__ (self, text, answer, **kwargs):
        deskbar.interfaces.Match.__init__ (self, name = text,
                icon = "gtk-add", category = "calculator", **kwargs)
        self.answer = str (answer)
        self.add_action (CalculatorAction (text, self.answer))

    def get_hash (self):
        return self.answer

class CalculatorModule (deskbar.interfaces.Module):
    
    INFOS = {"icon": deskbar.core.Utils.load_icon ("gtk-add"),
             "name": _("Calculator"),
             "description": _("Calculate simple equations"),
             "version" : VERSION,
             "categories" : { "calculator" : { "name" : _("Calculator") }}}

    def __init__ (self):
        deskbar.interfaces.Module.__init__ (self)
        self.hexre = re.compile ("0[Xx][0-9a-fA-F_]*[0-9a-fA-F]")
        self.binre = re.compile ("0[bB][01_]*[01]")

    def _number_parser (self, match, base):
        """A generic number parser, regardless of base. It also ignores the
        '_' character so it can be used as a separator. Note how we skip
        the first two characters since we assume it is something like '0x'
        or '0b' and identifies the base."""
        table = { '0' : 0, '1' : 1, '2' : 2, '3' : 3, '4' : 4,
                  '5' : 5, '6' : 6, '7' : 7, '8' : 8, '9' : 9,
                  'a' : 10, 'b' : 11, 'c' : 12, 'd' : 13,
                  'e' : 14, 'f' : 15 }
        d = 0
        for c in match.group()[2:]:
            if c != "_":
                d = d * base + table[c]
        return str (d)

    def _binsub (self, match):
        """Because python doesn't handle binary literals, we parse it
        ourselves and replace it with a decimal representation."""
        return self._number_parser (match, 2)

    def _hexsub (self, match):
        """Parse the hex literal ourselves. We could let python do it, but
        since we have a generic parser we use that instead."""
        return self._number_parser (match, 16)

    def run_query (self, query):
       """We evaluate the equation by first replacing hex and binary literals
       with their decimal representation. (We need to check hex, so we can
       distinguish 0x10b1 as a hex number, not 0x1 followed by 0b1.) We
       severely restrict the eval environment.  Any errors are ignored."""
       restricted_dictionary = { "__builtins__" : None, "abs" : abs,
                                 "acos" : math.acos, "asin"   : math.asin,
                                 "atan" : math.atan, "atan2"  : math.atan2,
                                 "bin"  : lenient_bin,"ceil"  : math.ceil,
                                 "cos"  : math.cos,  "cosh"   : math.cosh,
                                 "degrees" : math.degrees,
                                 "exp"  : math.exp,  "floor"  : math.floor,
                                 "hex"  : lenient_hex, "int"  : int,
                                 "log"  : math.log,  "pow"    : math.pow,
                                 "log10" : math.log10, "oct"  : lenient_oct,
                                 "pi"   : math.pi,  "radians" : math.radians,
                                 "round": round,     "sin"    : math.sin,
                                 "sinh" : math.sinh, "sqrt" : math.sqrt,
                                 "tan"  : math.tan,  "tanh" : math.tanh}
       try:
            scrubbedquery = query.lower()
            scrubbedquery = self.hexre.sub (self._hexsub, scrubbedquery)
            scrubbedquery = self.binre.sub (self._binsub, scrubbedquery)
            for (c1, c2) in (("[", "("), ("{", "("), ("]", ")"), ("}", ")")):
                scrubbedquery = scrubbedquery.replace (c1, c2)

            answer = eval (scrubbedquery, restricted_dictionary)

            # Try and avoid echoing back simple numbers. Note that this
            # doesn't work well for floating point, e.g. '3.' behaves badly.
            if str (answer) == query:
                return None
            
            # We need this check because the eval can return function objects
            # when we are halfway through typing the expression.
            if isinstance (answer, (float, int, long, str)):
                return answer
            else:
                return None
       except Exception, e:
           LOGGER.debug (str(e))
           return None
    
    def query (self, query):
		answer = self.run_query(query)
		if answer != None:
			result = [CalculatorMatch (query, answer)]
			self._emit_query_ready (query, result)
			return answer
		else:
			return []

