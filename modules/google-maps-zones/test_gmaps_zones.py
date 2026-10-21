"""Tests for the parts that need neither Google nor Home Assistant: pytest test_gmaps_zones.py"""
import json, os, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gmaps_zones as g

CFG = {**g.DEFAULTS, "icons": {"★": "mdi:star", "Want to go": "mdi:flag"}}  # icons order = which list wins
Z = lambda i, n, lat=1.0: {"id": i, "name": n, "latitude": lat, "longitude": 1.0, "icon": "mdi:flag", "radius": 30,
                           "passive": False}
W = lambda n, lat=1.0: {"name": n, "latitude": lat, "longitude": 1.0, "icon": "mdi:flag", "radius": 30, "passive": False}


def test_parse_getlist():
    entry = lambda name, lat, lng: [None, [None, None, "", None, "1 Main St", [None, None, lat, lng]], name, ""]
    body = ")]}'\n" + json.dumps([[["id"], 1, [1], ["me"], "Want to go", "", None, None,
                                   [entry("Bar A", 10.1, 20.1), entry("", 10.2, 20.2)]]])
    assert g.parse_getlist(body) == ("Want to go", [{"name": "Bar A", "addr": "1 Main St", "lat": 10.1, "lng": 20.1},
                                                    {"name": "1 Main St", "addr": "1 Main St", "lat": 10.2, "lng": 20.2}])


def test_coords_from_url():
    pin = "https://www.google.com/maps/place/X/@10.0,20.0,19z/data=!3m1!8m2!3d10.0012345!4d20.0054321"
    assert g.coords_from_url(pin) == (10.0012345, 20.0054321)  # the pin, not the map centre
    area = "https://www.google.com/maps/place/Some+Area/@10,20,15z/data=!4m6!3m5!8m2!3d10.5!4d20.5!16s!5m1!3d1.0!4d-19.6"
    assert g.coords_from_url(area) == (10.5, 20.5)  # an area carries other !3d!4d pairs: only the pin counts
    assert g.coords_from_url("https://www.google.com/maps/place/X/@10.4,20.2,17z/data=!3m1") == (10.4, 20.2)
    assert g.coords_from_url("https://www.google.com/maps/place/X/@10.4,-19.6,3z/data=!3m1") is None  # world view
    assert g.coords_from_url("https://www.google.com/maps/@10.4,20.2,12z") is None  # not a place page


def test_empty_list_rows_in_any_language():
    assert g.empty_list_row("Trips\nPrivate · 0 places") and g.empty_list_row("Viajes\nLista privada · 0 sitios")
    assert not g.empty_list_row("Want to go\nPrivate · 10 places") and not g.empty_list_row("Bars\nShared · 3 places")


def test_wanted_zones_dedupes_skips_home_and_ranks_lists():
    lists = {"Want to go": [{"name": "Bar A", "lat": 10.0, "lng": 20.0}, {"name": "Bar B", "lat": 10.0001, "lng": 20.0},
                            {"name": "Near home", "lat": 30.00005, "lng": 40.0}],
             "★": [{"name": "Bar A", "lat": 10.0, "lng": 20.0}, {"name": "Museum", "lat": 11.0, "lng": 21.0}]}
    w = g.wanted_zones(lists, CFG, home=(30.0, 40.0))
    assert [z["name"] for z in w] == ["Bar A", "Museum", "Bar B"]  # Bar B is 11 m from Bar A: both kept
    assert w[0]["icon"] == "mdi:star" and w[2]["icon"] == "mdi:flag"  # Bar A takes the star: ★ ranks first


def test_plan_only_touches_owned_zones():
    zones = [Z("a", "Kept"), Z("b", "Moved", lat=1.5), Z("c", "Unsaved"), Z("mine", "Gym")]
    p = g.plan([W("Kept"), W("Moved", lat=1.6), W("New"), W("Gym")], zones, owned={"a", "b", "c"}, adopt=False)
    assert [x["name"] for x in p["create"]] == ["New"]
    assert [x["zone_id"] for x in p["update"]] == ["b"]
    assert p["delete"] == ["c"]
    assert p["skipped"] == ["Gym"]  # the user's own zone with that name is left alone, no duplicate made
    assert g.plan([W("Kept", lat=1.0000004)], zones, owned={"a"}, adopt=False)["update"] == []  # rounding, not a move
    # a place seen in its list but not located this time (an area without a pin) keeps its zone
    p = g.plan([W("Kept")], zones, owned={"a", "b", "c"}, adopt=False, protect={"Moved"})
    assert p["delete"] == ["c"] and "b" in p["keep"]


def test_first_run_takes_over_zones_by_name_or_position():
    zones = [{**Z("x", "1 Main St, 00000 Town, Country"), "latitude": 10.0}]
    p = g.plan([{**W("1 Main St"), "latitude": 10.000045}], zones, owned=set(), adopt=True)  # 5 m away, shorter name
    assert p["create"] == [] and p["keep"] == {"x"} and p["update"][0]["name"] == "1 Main St"


def test_excluded_places_never_get_through():
    lists = {"★": [{"name": "1 Old Street", "lat": 1, "lng": 1}, {"name": "Bar", "lat": 2, "lng": 2}],
             g.LABELLED: [{"name": "Old home", "addr": "Old home 9 Old Street", "lat": 3, "lng": 3}]}
    kept, unread = g.drop_excluded(lists, ["7 old street", "Area"], [r"old\s+street"])
    assert kept == {"★": [{"name": "Bar", "lat": 2, "lng": 2}], g.LABELLED: []} and unread == ["Area"]


def test_due_on_button_press_and_daily_not_on_first_look():
    cfg, st = {**CFG, "daily_at": "04:45"}, {}
    night, morning = datetime(2026, 1, 2, 1, 0), datetime(2026, 1, 2, 5, 0)
    assert g.due(cfg, st, night, "t1") == ""        # first look only remembers the button
    assert g.due(cfg, st, night, "t1") == ""        # not pressed since
    assert g.due(cfg, st, night, "t2") == "button"  # pressed
    assert g.due(cfg, st, morning, "t2") == "daily" and g.due(cfg, st, morning, "t2") == ""  # once a day


def test_load_config_fills_defaults(tmp_path):
    p = tmp_path / "gmaps_zones.json"
    p.write_text(json.dumps({"home_assistant": {"url": "http://ha:8123"}, "exclude": ["x"]}))
    c = g.load_config(str(p))
    assert c["home_assistant"] == {"url": "http://ha:8123", "token_env": "HA_TOKEN"} and c["radius"] == 30
    assert c["_state"].endswith("gmaps_zones-state.json") and c["_last_read"].endswith("gmaps_zones-last-read.json")
