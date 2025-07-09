"""
Tests for flow.py: token splitting and route parsing.
"""

import pytest
from summoner.protocol.flow import get_token_list, Flow
from summoner.protocol.process import Node, ParsedRoute


@pytest.mark.parametrize("input_str, sep, expected", [
    ("foo,bar(baz,qux),zap", ",", ["foo", "bar(baz,qux)", "zap"]),
    (" a , b ,c ", ",", ["a", "b", "c"]),
    ("one(two,three,four),five", ",", ["one(two,three,four)", "five"]),
])
def test_get_token_list(input_str, sep, expected):
    # Only top-level separators should split
    assert get_token_list(input_str, sep) == expected


def make_flow():
    # Helper to set up a Flow with two arrow styles
    flow = Flow()
    flow.activate()
    flow.add_arrow_style(stem="-", brackets=("[", "]"), separator=",", tip=">")
    flow.add_arrow_style(stem="=", brackets=("{", "}"), separator=";", tip=")")
    flow.ready()
    return flow


def test_parse_route_complete_labeled():
    flow = make_flow()
    pr = flow.parse_route("A --> B")
    # Expect source A, no label, target B
    assert pr.source == (Node("A"),)
    assert pr.label == ()
    assert pr.target == (Node("B"),)
    assert pr.is_arrow


def test_parse_route_unlabeled_complete():
    flow = make_flow()
    pr = flow.parse_route("X--[]-->Y")
    assert pr.source == (Node("X"),)
    assert pr.target == (Node("Y"),)


def test_parse_route_dangling_right():
    flow = make_flow()
    pr = flow.parse_route("-->B")
    # Dangling left: no source, no label
    assert pr.source == ()
    assert pr.target == (Node("B"),)
    assert pr.is_initial


def test_parse_route_dangling_left():
    flow = make_flow()
    pr = flow.parse_route("A-->")
    assert pr.source == (Node("A"),)
    assert pr.target == ()


def test_parse_route_standalone():
    flow = make_flow()
    pr = flow.parse_route("X, Y ,Z")
    # Comma-separated standalone objects
    assert pr.source == (Node("X"), Node("Y"), Node("Z"))
    assert not pr.is_arrow and pr.is_object


def test_parse_route_invalid_token():
    flow = make_flow()
    with pytest.raises(ValueError):
        flow.parse_route("A --> inv&alid")


def test_parse_routes_list():
    flow = make_flow()
    routes = ["A-->B", "C"]
    prs = flow.parse_routes(routes)
    assert isinstance(prs, list)
    assert prs[0] == flow.parse_route("A-->B")
    assert prs[1] == flow.parse_route("C")
    