#!/usr/bin/env python
#
# test_calculator.py : Tests for the deskbar calculator handler
#
# Copyright (C) 2006 by Callum McKenzie
#
# Time-stamp: <2007-10-05 18:37:08 callum>
#

import unittest
import re
from math import pi
import calculator

class CalculatorBinTest (unittest.TestCase):
    # Testing the bin function
    def testBinZero (self):
        self.assertEqual (calculator.bin (0), "0b0")
    def testBinPositive (self):
        self.assertEqual (calculator.bin (42), "0b101010")
        self.assertEqual (calculator.bin (511), "0b111111111")
    def testBinNegative (self):
        self.assertEqual (calculator.bin (-2),
                         "0b...1110")
        self.assertEqual (calculator.bin (-1),
                         "0b...111")
    def testBinBigPositive (self):
        self.assertEqual (calculator.bin (4294967296L),
                          "0b100000000000000000000000000000000")
        self.assertEqual (calculator.bin (11453246122L),
                          "0b1010101010101010101010101010101010")
    def testBinBigNegative (self):
        self.assertEqual (calculator.bin (-4294967296L),
                          "0b...11100000000000000000000000000000000")
        self.assertEqual (calculator.bin (-11453246123L),
                          "0b...1110101010101010101010101010101010101")
    def testBinType (self):
        self.assertRaises (TypeError, calculator.bin, "42")
        self.assertRaises (TypeError, calculator.bin, 1.0)        

class CalculatorModuleTest (unittest.TestCase):
    def testHexRe (self):
        h = calculator.CalculatorModule ()
        self.failUnless (h.hexre.match ("0x12"))
        self.failUnless (h.hexre.match ("0X12"))
        self.failUnless (h.hexre.match ("0x0123456789abcdef"))
        self.failUnless (h.hexre.match ("0x0123456789ABCDEF"))        
        self.failUnless (h.hexre.match ("0xfedcba9876543210"))
        self.failUnless (h.hexre.match ("0xFEDCBA9876543210"))        
        self.failUnless (h.hexre.match ("0xfedc_ba98_7654_3210"))
        self.failUnless (h.hexre.match ("0x_fedc_ba98_7654_3210"))
        self.failIf (h.hexre.match ("0x_"))
        self.failIf (h.hexre.match ("x1234"))
        self.failIf (h.hexre.match ("cafebabe"))
        self.failIf (h.hexre.match ("Purple"))

    def testBinRe (self):
        h = calculator.CalculatorModule ()
        self.failUnless (h.binre.match ("0b10"))
        self.failUnless (h.binre.match ("0B10"))
        self.failUnless (h.binre.match ("0b01101100"))
        self.failUnless (h.binre.match ("0b0110_1100"))
        self.failUnless (h.binre.match ("0b_0110_1100"))
        self.failUnless (h.binre.match ("0b11111111111111111111111111111111"))
        self.failUnless (h.binre.match ("0b1111111111111111111111111111111111111111111111111111111111111111"))
        self.failUnless (h.binre.match ("0b11111111111111111111111111111111111111111111111111111111111111111"))        
        self.failUnless (h.binre.match ("0b1111111111_111111111111111__111111111111111111111___1111111111"))        
        self.failIf (h.binre.match ("b1000"))
        self.failIf (h.binre.match ("b1234"))        
        self.failIf (h.binre.match ("1010101"))
        self.failIf (h.binre.match ("Purple"))

    def testHexSub (self):
        h = calculator.CalculatorModule ()
        match = h.hexre.match ("0x2f")
        self.assertEqual (h._hexsub (match), '47')
        match = h.hexre.match ("0xee789a45")
        self.assertEqual (h._hexsub (match), '4000881221')
        match = h.hexre.match ("0xee78_9a45")
        self.assertEqual (h._hexsub (match), '4000881221')
        match = h.hexre.match ("0x2f34897ef98d8922")
        self.assertEqual (h._hexsub (match), '3401494797017254178')
        match = h.hexre.match ("0x2f34897ef98d89226c")
        self.assertEqual (h._hexsub (match), '870782668036417069676')

    def testBinSub (self):
        h = calculator.CalculatorModule ()
        match = h.binre.match ("0b0")
        self.assertEqual (h._binsub (match), "0")
        match = h.binre.match ("0b101010")
        self.assertEqual (h._binsub (match), "42")
        match = h.binre.match ("0b11111111111111111111111111111111")
        self.assertEqual (h._binsub (match), "4294967295")
        match = h.binre.match ("0b100000000000000000000000000000001")
        self.assertEqual (h._binsub (match), "4294967297")
        match = h.binre.match ("0b_")
        self.assertEqual (match, None)
        match = h.binre.match ("0b101_010")
        self.assertEqual (h._binsub (match), "42")
        match = h.binre.match ("0b1111_1111_1111_1111_1111_1111_1111_1111")
        self.assertEqual (h._binsub (match), "4294967295")
        match = h.binre.match ("0b1____000000000000_00___000000000000000001")
        self.assertEqual (h._binsub (match), "4294967297")

    def testQuery (self):
        """Generic tests of the query function that don't fit anywhere else."""
        h = calculator.CalculatorModule ()
        self.assertEqual (h.query ("print 'Hello World'"), [])
        # Don't echo back simple identities ...
        self.assertEqual (h.query ("1"), [])
        # ... but do base conversions.
        self.assertEqual (h.query ("0x2"), 2)
        # This makes sure that hex, oct and bin always do the right
        # thing in the presence of fractions.
        self.assertEqual (h.query ("hex(0x5/2)"), "0x2")
        self.assertEqual (h.query ("oct(05/2)"), "02")
        self.assertEqual (h.query ("bin(0b101/2)"), "0b10")
        # Make sure that we accept all brackets.
        self.assertEqual (h.query ("abs(-1)"), 1)
        self.assertEqual (h.query ("abs[-1]"), 1)
        self.assertEqual (h.query ("abs{-1}"), 1)        
        # Now test some "complex" equations to check that bracketing
        # roks and try and provoke other issues.
        self.assertEqual (h.query ("1 + 3*(2+3)"), 16)
        self.assertEqual (h.query ("1 + 2*(2 - (3 - 2))"), 3)
        self.assertAlmostEqual (h.query ("sqrt(sin(pi/2)**2 + cos(pi/2)**2)"), 1.0)
        self.assertAlmostEqual (h.query ("sqrt(2)**sqrt(3)"), 1.8226346549)
        self.assertAlmostEqual (h.query ("1/(2 + log(3)) + atan(3)"), 1.571770885)
        
    def testQueryOperators (self):
        h = calculator.CalculatorModule ()
        self.assertEqual (h.query ("1 + 1"), 2)
        self.assertEqual (h.query ("2 - 4"), -2)
        self.assertEqual (h.query ("3 * 7"), 21)
        self.assertEqual (h.query ("35 / 5"), 7)
        self.assertEqual (h.query ("35 / 2"), 17.5)        
        self.assertEqual (h.query ("6 % 4"), 2)
        self.assertEqual (h.query ("-6 % 4"), 2)        
        self.assertEqual (h.query ("3 // 2"), 1)
        self.assertEqual (h.query ("-3 // 2"), -2)
        self.assertEqual (h.query ("3 << 3"), 24)
        self.assertEqual (h.query ("1 << 65"), 36893488147419103232)
        self.assertEqual (h.query ("8 >> 3"), 1)
        self.assertEqual (h.query ("8 >> 4"), 0)
        self.assertEqual (h.query ("-1 >> 3"), -1)
        self.assertEqual (h.query ("7 & 3"), 3)
        self.assertEqual (h.query ("-1 & 6"), 6)
        self.assertEqual (h.query ("8 & 3"), 0)
        self.assertEqual (h.query ("36893488147419103233 & 1"), 1)
        self.assertEqual (h.query ("8 | 4"), 12)
        self.assertEqual (h.query ("-1 | 5"), -1)
        self.assertEqual (h.query ("7 | 3"), 7)
        self.assertEqual (h.query ("36893488147419103232 | 1"),
                          36893488147419103233)
        self.assertEqual (h.query ("1 ^ 3"), 2)
        self.assertEqual (h.query ("7 ^ 7"), 0)
        self.assertEqual (h.query ("-1 ^ 3"), -4)
        self.assertEqual (h.query ("36893488147419103233 ^ 1"),
                          36893488147419103232)
        self.assertEqual (h.query ("~3"), -4)
        self.assertEqual (h.query ("~36893488147419103233"),
                          -36893488147419103234)
        self.assertEqual (h.query ("~-1"), 0)
        self.assertEqual (h.query ("~-36893488147419103234"),
                          36893488147419103233)
        self.assertEqual (h.query ("~~5"), 5)
        self.assertEqual (h.query ("~~-5"), -5)

    def testQueryConversions (self):
        h = calculator.CalculatorModule ()
        # Start off with some simple stuff even though these have
        # _theoretically_ been tested above.
        self.assertEqual (h.query ("0x10"), 16)
        self.assertEqual (h.query ("0xabcd"), 43981)
        self.assertEqual (h.query ("0x2f34897ef98d89226c"),
                          870782668036417069676)
        self.assertEqual (h.query ("-0x10"), -16)

        self.assertEqual (h.query ("0b101"), 5)
        self.assertEqual (h.query ("-0b101"), -5)
        self.assertEqual (h.query ("-0b100000000000000000000000000000001"),
                          -4294967297)

        # Octal hasn't been exercised above.
        self.assertEqual (h.query ("0123"), 83)        
        self.assertEqual (h.query ("01234567012345670123456701234567"),
                          1616895878810725189668911479)
        self.assertEqual (h.query ("-0123"), -83)        

        # Floating point identities.
        self.assertEqual (h.query ("0.12345 + 0"), 0.12345)
        self.assertEqual (h.query ("-0.12345 + 0"), -0.12345)
        self.assertEqual (h.query ("-0.12e5 + 0"), -0.12e5)
        self.assertEqual (h.query ("0.12e-5 + 0"), 0.12e-5)        

        # Now do the really stupid case.
        self.assertEqual (h.query ("-10 + 0"), -10)
        self.assertEqual (h.query ("12345678901234567890 + 0"),
                          12345678901234567890)        
        
        # Test that this is counted as one hex literal rather than
        # one hex literal followed by a binary literal.
        self.assertEqual (h.query ("0x10b1"), 4273)

    def testQueryFunctions (self):
        h = calculator.CalculatorModule ()
        # These aren't so much a test of cosine, as a test of
        # general parsing prinicples.
        self.assertAlmostEqual (h.query ("cos(0)"), 1.0, 3)
        self.assertAlmostEqual (h.query ("cos(0.0)"), 1.0, 3)        
        self.assertAlmostEqual (h.query ("cos (0)"), 1.0, 3)
        self.assertAlmostEqual (h.query ("CoS(0)"), 1.0, 3)
        # We require brackets for functions.
        self.assertEqual (h.query ("cos 0"), [])
        self.assertEqual (h.query ("cosine(0)"), [])        
        # Now for the rest of the functions.
        self.assertAlmostEqual (h.query ("asin(0.0)"), 0.0, 3)        
        self.assertAlmostEqual (h.query ("acos(1.0)"), 0.0, 3)        
        self.assertAlmostEqual (h.query ("atan2(1.0, 0.0)"), pi/2.0, 3)
        self.assertAlmostEqual (h.query ("atan2(0.0, 1.0)"), 0.0, 3)
        self.assertAlmostEqual (h.query ("atan2(-1.0, 1.0)"), -pi/4.0, 3)
        self.assertAlmostEqual (h.query ("sinh(0.0)"), 0.0, 3)        
        self.assertAlmostEqual (h.query ("cosh(0.0)"), 1.0, 3)        
        self.assertAlmostEqual (h.query ("tanh(0.0)"), 0.0, 3)
        self.assertAlmostEqual (h.query ("sin(0.0)"), 0.0, 3)
        self.assertAlmostEqual (h.query ("cos(pi/2)"), 0.0, 3)
        self.assertAlmostEqual (h.query ("tan(pi/4)"), 1.0, 3)
        self.assertAlmostEqual (h.query ("abs(-1.0)"), 1.0, 3)
        self.assertAlmostEqual (h.query ("sqrt(2.0)"), 1.41421, 3)
        self.assertAlmostEqual (h.query ("pi"), 3.14159, 3)
        self.assertAlmostEqual (h.query ("log10(345)"), 2.537819, 3)
        self.assertAlmostEqual (h.query ("log(pi)"), 1.1447299, 3)
        self.assertAlmostEqual (h.query ("exp(1.0)"), 2.718282, 3)
        self.assertAlmostEqual (h.query ("radians(180)"), pi, 3)
        self.assertAlmostEqual (h.query ("degrees(-pi/2)"), -90, 3)
        self.assertAlmostEqual (h.query ("ceil(2.3)"), 3.0, 3)
        self.assertAlmostEqual (h.query ("ceil(-2.3)"), -2.0, 3)
        self.assertAlmostEqual (h.query ("floor(2.3)"), 2.0, 3)
        self.assertAlmostEqual (h.query ("floor(-2.3)"), -3.0, 3)
        self.assertAlmostEqual (h.query ("round(2.3)"), 2.0, 3)
        self.assertAlmostEqual (h.query ("round(-2.3)"), -2.0, 3)
        self.assertEqual (h.query ("int(2.3)"), 2)
        self.assertEqual (h.query ("int(-2.3)"), -2)

unittest.main ()
