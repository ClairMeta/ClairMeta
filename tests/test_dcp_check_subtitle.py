# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information

import os
import shutil
import tempfile
import unittest
from types import SimpleNamespace

from clairmeta.dcp_check_subtitle import Checker
from clairmeta.logger import disable_log

# SpotNumber is optional in SMPTE ST 428-7 (see DCDMSubtitle-2014.xsd).
# Each subtitle below omits it and is crafted to make a check report an
# error, so that the error message formatting code paths are exercised.
SMPTE_SUBTITLE_WITHOUT_SPOT_NUMBER = """<?xml version="1.0" encoding="UTF-8"?>
<SubtitleReel xmlns="http://www.smpte-ra.org/schemas/428-7/2014/DCST">
  <Id>urn:uuid:26d23576-6f82-4353-a631-90e59a12cd84</Id>
  <ContentTitleText>Blank</ContentTitleText>
  <ReelNumber>1</ReelNumber>
  <Language>fr</Language>
  <EditRate>24 1</EditRate>
  <TimeCodeRate>24</TimeCodeRate>
  <StartTime>00:00:00:00</StartTime>
  <LoadFont ID="MinRefFont">urn:uuid:21124f67-258b-4d6f-9f4c-d40c3a26700a</LoadFont>
  <SubtitleList>
    <Font ID="MinRefFont">
      <Subtitle TimeIn="00:00:04:00" TimeOut="00:00:04:00">
        <Text>Null duration</Text>
      </Subtitle>
      <Subtitle TimeIn="00:00:05:00" TimeOut="00:00:06:00">
        <Text VAlign="top" VPosition="0">Out of screen</Text>
      </Subtitle>
      <Subtitle TimeIn="00:00:07:00" TimeOut="00:00:08:00">
        <Text>1</Text><Text>2</Text><Text>3</Text><Text>4</Text>
        <Text>5</Text><Text>6</Text><Text>7</Text>
      </Subtitle>
      <Subtitle TimeIn="00:00:09:00" TimeOut="00:00:10:00">
      </Subtitle>
    </Font>
  </SubtitleList>
</SubtitleReel>
"""


class SubtitleSpotNumberTest(unittest.TestCase):
    def setUp(self):
        disable_log()
        self.folder = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.folder)

        xml_name = "subtitle.xml"
        with open(os.path.join(self.folder, xml_name), "w", encoding="utf-8") as f:
            f.write(SMPTE_SUBTITLE_WITHOUT_SPOT_NUMBER)

        dcp = SimpleNamespace(path=self.folder, schema="SMPTE")
        self.checker = Checker(dcp)
        self.asset = ("Subtitle", {"Path": xml_name})

    def run_subtitle_check(self, check):
        self.checker.run_check(check, None, self.asset, self.folder)
        return self.checker.checks[-1]

    def assert_check_reports(self, check, expected_messages):
        check_exec = self.run_subtitle_check(check)
        error_names = [e.name for e in check_exec.errors]
        self.assertNotIn("internal_error", error_names)
        messages = [e.message for e in check_exec.errors]
        for expected in expected_messages:
            self.assertIn(expected, messages)

    def test_st_timing(self):
        self.assert_check_reports(
            self.checker.check_subtitle_cpl_st_timing,
            ["Subtitle 00:00:04:00 null or negative duration"],
        )

    def test_position(self):
        self.assert_check_reports(
            self.checker.check_subtitle_cpl_position,
            ["Subtitle 00:00:05:00 is out of screen (top)"],
        )

    def test_max_elements(self):
        self.assert_check_reports(
            self.checker.check_subtitle_cpl_max_elements,
            ["Too many Text elements (7, maximum is 6) for subtitle 00:00:07:00"],
        )

    def test_content(self):
        self.assert_check_reports(
            self.checker.check_subtitle_cpl_content,
            ["Subtitle 00:00:09:00 element must define one Text or Image"],
        )


if __name__ == "__main__":
    unittest.main()
