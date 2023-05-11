import json
import dataclasses
from typing import Dict, Union, Optional, Any
from json import JSONEncoder
from mygfa import mygfa


SimpleType = Optional[Dict[str, Union[bool, str, int]]]


class GenericSimpleEncoder(JSONEncoder):
    """A generic JSON encoder for mygfa graphs."""

    def default(self, o: Any) -> SimpleType:
        if isinstance(o, mygfa.Path):
            items = str(o).split("\t")
            return {"segments": items[2], "overlaps": items[3]}
        if isinstance(o, mygfa.Link):
            return {
                "from": o.from_.name,
                "from_orient": o.from_.ori,
                "to": o.to_.name,
                "to_orient": o.to_.ori,
                "overlap": str(o.overlap),
            }
        if isinstance(o, (mygfa.Segment, mygfa.Alignment)):
            return dataclasses.asdict(o)
        return None


def simple(graph: mygfa.Graph) -> None:
    """Prints a "wholesale dump" JSON representation of `graph`"""
    print(json.dumps(graph.headers, indent=4))
    print(json.dumps(graph.segments, indent=4, cls=GenericSimpleEncoder))
    print(json.dumps(graph.links, indent=4, cls=GenericSimpleEncoder))
    print(json.dumps(graph.paths, indent=4, cls=GenericSimpleEncoder))
