# import os
# current_dir = os.getcwd()
# test_dir = f"{current_dir}{os.path.sep}tests"
# os.chdir(test_dir)
# current_dir = os.getcwd()
# # some_file.py
# import sys
# # insert at 1, 0 is the script path (or '' in REPL)
# sys.path.insert(1, current_dir)

import unittest
from stoscbots.db import db

class TestDB(unittest.TestCase):
    def setUp(self):
        pass

    def test_get_next_services(self):
        services = db.get_next_services()
        self.assertGreater(len(services), 0)

    def test_get_bday_weekly(self):
        start, end, result = db.get_bday(duration = 'w')
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertGreaterEqual(len(result),0)

    def test_get_anniversaries_weekly(self):
        start, end, result = db.get_anniversaries(duration = 'w')
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertGreaterEqual(len(result),0)
    
    def test_get_bday_daily(self):
        start, end, result = db.get_bday(duration = 'd')
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertGreaterEqual(len(result),0)

    def test_get_anniversaries_daily(self):
        start, end, result = db.get_anniversaries(duration = 'd')
        self.assertIsNotNone(start)
        self.assertIsNotNone(end)
        self.assertGreaterEqual(len(result),0)

    def test_get_members_for_area(self):
        memberlist,area_name = db.get_members_for_area('2')
        self.assertEqual(memberlist[0][0], 'Aaron K Mathew (A053)')
        self.assertEqual(len(memberlist),46)
        self.assertEqual(area_name[0][0], 'Houg|Sengk|Pungg')

    def test_get_member_details_code(self):
        result = db.get_member_details('V019','code')
        self.assertEquals(result[0][1], 'Vibin Joseph Kuriakose (V019)')

    def test_get_member_details_free_text(self):
        result = db.get_member_details('Vibin','free_text')
        self.assertEquals(result[0][1], 'Vibin Joseph Kuriakose (V019)')

    def test_get_booking_GUID(self):
        result = db.get_booking_GUID('T047')
        self.assertEquals(len(result), 0)

    def test_get_members_for_serviceID(self):
        result = db.get_members_for_serviceID('1')
        self.assertEquals(result[0], 'Sun Morning English')
        self.assertEquals(result[1], 'Sun, Jun 28 08:30 AM')
        self.assertEquals(len(result), 4)

    def test_get_members_born_on(self):
        result = db.get_members_born_on('1979')
        self.assertEquals(result[25][2], 'Vibin Joseph Kuriakose (V019)')
        self.assertEquals(len(result), 26)

    def test_get_gb_ineligible(self):
        result = db.get_gb_ineligible()
        self.assertIsNotNone(result)

if __name__ == '__main__':
    unittest.main()