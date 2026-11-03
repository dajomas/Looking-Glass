import pytest
from looking_glass.services.scrying_glass_matches import expand_matches

def result(slug="04-silent-room",status="setup_not_found"):
    return {"campaign_id":"1","campaign_name":"Crypt","room_name":"04 - Silent room","setup_name":slug,"matched":status=="matched","status":status,"message":"old"}

def payload(names):
    return {"campaigns":[{"id":"2","name":"Other","setups":["04-silent-room-secret"]},{"id":"1","name":"Crypt","setups":names}]}

def test_multiple_variants_exact_first_and_deduplication():
    names=["04-silent-room-5-6","04-silent-room-1-4","04-silent-room","04-silent-room-reinforcements","04-silent-room-1-4"]
    actual=expand_matches(result(),payload(names))
    assert actual["setup_names"]==["04-silent-room","04-silent-room-1-4","04-silent-room-5-6","04-silent-room-reinforcements"]
    assert actual["match_count"]==4 and actual["exact_match"] and actual["matched"]
    assert actual["status"]=="matched" and "4 matching" in actual["message"]
    assert actual["setup_name"]=="04-silent-room"

@pytest.mark.parametrize("name",["04-silent-roommate","04-silent-room2","004-silent-room","04-silent-rooms-1-4","other-04-silent-room-1-4","04-silent-room-", "04-SILENT-room-1-4"])
def test_boundary_and_canonical_case(name):
    actual=expand_matches(result(),payload([name]))
    assert not actual["matched"] and actual["setup_names"]==[] and actual["match_count"]==0

def test_single_variant_no_assumptions_about_suffix():
    actual=expand_matches(result(),payload(["04-silent-room-night"]));assert actual["setup_names"]==["04-silent-room-night"]
    assert not actual["exact_match"] and actual["match_count"]==1

@pytest.mark.parametrize("status",["campaign_not_accessible","ambiguous_campaign","invalid_room_name","disabled","unnamed_room"])
def test_access_and_validation_failures_are_preserved(status):
    actual=expand_matches(result(status=status),payload(["04-silent-room-1-4"]))
    assert actual["status"]==status and actual["setup_names"]==[]

def test_empty_prefix_never_matches_everything():
    assert not expand_matches(result(slug=""),payload(["04-silent-room"]))["matched"]

def test_other_campaign_never_leaks():
    actual=expand_matches(result(),payload([]));assert not actual["matched"]
    assert "secret" not in str(actual)

def test_exact_only_remains_supported():
    actual=expand_matches(result(status="matched"),payload(["04-silent-room"]))
    assert actual["exact_match"] and actual["match_count"]==1
