from plugins.handlers_area_prayer_groups import build_message


def test_get_area_prayer_group_members_no_members():
    # Test case with empty member list
    member_list = []
    area_name = [["Test Area"]]
    result = build_message(member_list, area_name)
    assert result == "No members in this area"


def test_get_area_prayer_group_members_():
    # Test case with multiple members in the list
    member_list = [
        ["John Doe (1234)"],
        ["Jane Smith (5678)"]
    ]
    area_name = [["Test Area"]]
    result = build_message(member_list, area_name)
    expected_result = (
        "**Members in Test Area** `(2)`\n\n"
        "• John Doe `(1234)`\n"
        "• Jane Smith `(5678)`"
    )
    assert result == expected_result
