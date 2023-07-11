from stoscbots.db import db
import pytest


def test_get_bday_weekly():
    start, end, result = db.get_bday(duration="w")
    assert start is not None
    assert end is not None
    assert len(result) >= 0


def test_get_anniversaries_weekly():
    start, end, result = db.get_anniversaries(duration="w")
    assert start is not None
    assert end is not None
    assert len(result) >= 0


def test_get_bday_daily():
    start, end, result = db.get_bday(duration="d")
    assert start is not None
    assert end is not None
    assert len(result) >= 0


def test_get_anniversaries_daily():
    start, end, result = db.get_anniversaries(duration="d")
    assert start is not None
    assert end is not None
    assert len(result) >= 0


def test_get_members_for_area():
    memberlist, area_name = db.get_members_for_area("2")
    assert memberlist[0][0] == "Ajish Samuel Thomas (A066)"
    assert area_name[0][0] == "Houg|Sengk|Pungg"


def test_get_member_details_code():
    result = db.get_member_details("V019", "code")
    assert result[0][2] == "Vibin Joseph Kuriakose"


def test_get_member_details_free_text():
    result = db.get_member_details("Vibin", "free_text")
    assert result[0][2] == "Vibin Joseph Kuriakose"


def test_get_members_born_on():
    result = db.get_members_born_on("1979")
    assert result[22][2] == "Vibin Joseph Kuriakose (V019)"


def test_get_gb_eligible_count_type():
    result = db.get_gb_eligible_count()
    assert isinstance(result[0][0], int)


def test_get_gb_eligible_count_greater_0():
    result = db.get_gb_eligible_count()
    assert result[0][0] > 0


def test_get_person_name():
    result = db.get_person_name("579")
    assert result[0][0] == "John "


def test_raises_exception_on_divide_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0
