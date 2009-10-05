#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
#    Copyright 2008, 2009, Lukas Lueg, lukas.lueg@gmail.com
#
#    This file is part of Pyrit.
#
#    Pyrit is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Pyrit is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Pyrit.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import with_statement

import pyrit_cli
from cpyrit import util, storage
import os
import random
import tempfile
import unittest


class Pyrit_CLI_TestFunctions(unittest.TestCase):

    def setUp(self):
        self.storage_path = tempfile.mkdtemp()
        self.tempfile = os.path.join(self.storage_path, 'testfile')
        self.cli = pyrit_cli.Pyrit_CLI()
        self.cli.storage = storage.Storage(self.storage_path)
        self.cli.verbose = False

    def tearDown(self):
        pass

    def _createPasswords(self, filename, count=2000):
        test_passwds = ['test123%i' % i for i in xrange(count-1)]
        test_passwds += ['dictionary']
        random.shuffle(test_passwds)
        with open(filename, 'w') as f:
            f.write('\n'.join(test_passwds))
        return test_passwds

    def _createDatabase(self, essid='linksys', count=2000):
        self.cli.create_essid(essid='linksys')
        self._createPasswords(self.tempfile, count)
        self.cli.import_passwords(self.tempfile)
        l = 0
        for results in util.StorageIterator(self.cli.storage, essid):
            l += len(results)
        self.assertEqual(l, count)

    def testListEssids(self):
        self.cli.create_essid(essid='test1234')
        self.cli.create_essid(essid='test1235')
        self.cli.list_essids()

    def testListCores(self):
        self.cli.list_cores()

    def testPrintHelp(self):
        self.cli.print_help()

    def testCreateAndDeleteEssid(self):
        # EssidStore should be empty
        self.assertEqual(len(self.cli.storage.essids), 0)
        self.assertFalse('testessid' in self.cli.storage.essids)
        # Add one ESSID
        self.cli.create_essid(essid='testessid')
        self.assertEqual(len(self.cli.storage.essids), 1)
        self.assertTrue('testessid' in self.cli.storage.essids)
        # EssidStore should be empty again
        self.cli.delete_essid(essid='testessid', confirm=False)
        self.assertEqual(len(self.cli.storage.essids), 0)
        self.assertTrue('testessid' not in self.cli.storage.essids)

    def testImportPasswords(self):
        self.assertEqual(len(self.cli.storage.passwords), 0)
        # valid_passwds should get accepted, short_passwds ignored
        valid_passwds = ['test123%i' % i  for i in xrange(100000)]
        short_passwds = ['x%i' % i for i in xrange(30000)]
        test_passwds = valid_passwds + short_passwds
        random.shuffle(test_passwds)
        with open(self.tempfile, 'w') as f:
            f.write('\n'.join(test_passwds))
        self.cli.import_passwords(filename=self.tempfile)
        new_passwds = set()
        for key, pwset in self.cli.storage.passwords.iteritems():
            new_passwds.update(pwset)
        self.assertEqual(new_passwds, set(valid_passwds))
        # There should be no duplicates
        random.shuffle(test_passwds)
        with open(self.tempfile, 'a') as f:
            f.write('\n')
            f.write('\n'.join(test_passwds))
        self.cli.import_passwords(filename=self.tempfile)
        new_passwds = set()
        i = 0
        for key, pwset in self.cli.storage.passwords.iteritems():
            new_passwds.update(pwset)
            i += len(pwset)
        self.assertEqual(i, len(valid_passwds))
        self.assertEqual(new_passwds, set(valid_passwds))

    def testAnalyze(self):
        self.cli.analyze(capturefile='wpapsk-linksys.dump')
        self.cli.analyze(capturefile='wpa2psk-linksys.dump')

    def testStripCapture(self):
        self.cli.stripCapture(capturefile='wpapsk-linksys.dump', \
                            filename=self.tempfile)
        parser = self.cli._getParser(self.tempfile)
        self.assertTrue('00:0b:86:c2:a4:85' in parser)
        self.assertEqual(parser['00:0b:86:c2:a4:85'].essid, 'linksys')
        self.assertTrue('00:13:ce:55:98:ef' in parser['00:0b:86:c2:a4:85'])
        self.assertTrue(parser['00:0b:86:c2:a4:85'].isCompleted())

    def testStripLive(self):
        self.cli.stripCapture(capturefile='wpa2psk-linksys.dump', \
                            filename=self.tempfile)
        parser = self.cli._getParser(self.tempfile)
        self.assertTrue('00:0b:86:c2:a4:85' in parser)
        self.assertEqual(parser['00:0b:86:c2:a4:85'].essid, 'linksys')
        self.assertTrue('00:13:ce:55:98:ef' in parser['00:0b:86:c2:a4:85'])
        self.assertTrue(parser['00:0b:86:c2:a4:85'].isCompleted())

    def testAttackPassthrough(self):
        self._createPasswords(self.tempfile)
        self.cli.attack_passthrough(filename=self.tempfile, \
                                    capturefile='wpapsk-linksys.dump')
        self.cli.attack_passthrough(filename=self.tempfile, \
                                    capturefile='wpa2psk-linksys.dump')

    def testAttackDB(self):
        self._createDatabase()
        self.cli.attack_db(capturefile='wpapsk-linksys.dump')
        self.cli.attack_db(capturefile='wpa2psk-linksys.dump')

    def testAttackBatch(self):
        self._createPasswords(self.tempfile)
        self.cli.import_passwords(filename=self.tempfile)
        self.cli.attack_batch(capturefile='wpapsk-linksys.dump')

    def testSelfTest(self):
        self.cli.selftest(timeout=3)

    def testBenchmark(self):
        self.cli.benchmark(timeout=3)

    def testBatch(self):
        test_passwds = self._createPasswords(self.tempfile)
        self.cli.import_passwords(self.tempfile)
        self.cli.create_essid('test1234')
        self.cli.batchprocess()
        self.assertEqual(len(self.cli.storage.passwords), \
                        len(self.cli.storage.essids.keys('test1234')))

    def testBatchWithFile(self):
        test_passwds = self._createPasswords(self.tempfile)
        self.cli.import_passwords(self.tempfile)
        self.cli.create_essid('test1234')
        self.cli.batchprocess(essid='test1234', filename=self.tempfile)
        self.assertEqual(len(self.cli.storage.passwords), \
                        len(self.cli.storage.essids.keys('test1234')))

    def testEval(self):
        self._createDatabase()
        self.cli.eval_results()

    def testVerify(self):
        self._createDatabase()
        self.cli.verify()

    def testExportPasswords(self):
        test_passwds = self._createPasswords(self.tempfile)
        self.cli.import_passwords(self.tempfile)
        self.cli.export_passwords(self.tempfile)
        with open(self.tempfile, 'r') as f:
            new_passwds = map(str.strip, f.readlines())
        self.assertEqual(sorted(test_passwds), sorted(new_passwds))

    def testExportCowpatty(self):
        self._createDatabase()
        self.cli.export_cowpatty(essid='linksys', filename=self.tempfile)
        fileresults = list(util.CowpattyReader(self.tempfile))
        dbresults = []
        for results in util.StorageIterator(self.cli.storage, 'linksys', \
                                            yieldNewResults=False):
            dbresults.extend(results)
        self.assertEqual(sorted(fileresults), sorted(dbresults))

    def testExportHashdb(self):
        self._createDatabase()
        os.unlink(self.tempfile)
        self.cli.export_hashdb(filename=self.tempfile)

if __name__ == "__main__":
    unittest.main()
