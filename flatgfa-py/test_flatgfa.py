import pytest
import flatgfa

TINY_GFA = b"""H	VN:Z:1.0
S	1	CAAATAAG
S	2	AAATTTTCTGGAGTTCTAT
S	3	TTG
S	4	CCAACTCTCTG
P	one	1+,2+,4-	*
P	two	1+,2+,3+,4-	*
L	1	+	2	+	0M
L	2	+	4	-	0M
L	2	+	3	+	0M
L	3	+	4	-	0M
"""


@pytest.fixture
def gfa():
    return flatgfa.parse_bytes(TINY_GFA)


def test_segs(gfa):
    # `gfa.segments` acts like a list.
    assert len(gfa.segments) == 4
    seg = gfa.segments[0]

    # An individual segment exposes its name and nucleotide sequence.
    assert seg.name == 1
    assert seg.sequence() == b"CAAATAAG"
    assert len(seg) == 8

    # You can also pull out the entire sequence of segments.
    seg = list(gfa.segments)[2]
    assert seg.name == 3

    # Use `str()` to get a GFA representation.
    assert str(seg) == "S	3	TTG"


def test_segs_find(gfa):
    # There is a method to find a segment by its name (with linear search).
    seg = gfa.segments.find(3)
    assert seg.id == 2
    assert seg.sequence() == b"TTG"


def test_paths(gfa):
    # `gfa.paths` similarly acts like a list.
    assert len(gfa.paths) == 2
    assert len(list(gfa.paths)) == 2

    # Individual paths expose their name (a bytestring).
    path = gfa.paths[0]
    assert path.name == "one"

    # GFA representation.
    assert str(path) == "P	one	1+,2+,4-	*"


def test_paths_find(gfa):
    # There is a method to find a path by its name.
    path = gfa.paths.find("two")
    assert path.id == 1
    assert path.name == "two"


def test_path_steps(gfa):
    # When you get a path, the path itself acts as a list of steps (handles).
    path = gfa.paths[1]
    assert len(path) == 4
    assert len(list(path)) == 4
    step = path[0]

    # A step (handle) is a reference to a segment and an orientation.
    assert step.segment.name == 1
    assert step.is_forward

    # GFA representation.
    assert str(step) == "1+"


def test_links(gfa):
    # You guessed it: `gfa.links` behaves as a list too.
    assert len(gfa.links) == 4
    assert len(list(gfa.links)) == 4
    link = gfa.links[1]

    # A link has a "from" handle and a "to" handle.
    assert link.from_.segment.name == 2
    assert link.from_.is_forward
    assert link.to.segment.name == 4
    assert not link.to.is_forward

    # GFA representation.
    assert str(link) == "L	2	+	4	-	0M"


def test_gfa_str(gfa):
    # You can serialize a graph as GFA text.
    assert str(gfa) == TINY_GFA.decode()


def test_read_write_gfa(gfa, tmp_path):
    # You can write FlatGFA objects as GFA text files.
    gfa_path = str(tmp_path / "tiny.gfa")
    gfa.write_gfa(gfa_path)
    with open(gfa_path, "rb") as f:
        assert f.read() == TINY_GFA

    # You can also parse GFA text files from the filesystem.
    new_gfa = flatgfa.parse(gfa_path)
    assert len(new_gfa.segments) == len(gfa.segments)


def test_read_write_flatgfa(gfa, tmp_path):
    # You can write FlatGFA graphs in our native binary format too.
    flatgfa_path = str(tmp_path / "tiny.flatgfa")
    gfa.write_flatgfa(flatgfa_path)

    # And read them back, which should be very fast indeed.
    new_gfa = flatgfa.load(flatgfa_path)
    assert len(new_gfa.segments) == len(gfa.segments)


def test_eq(gfa):
    # The various data components are equatable.
    assert gfa.segments[0] == gfa.segments[0]
    assert gfa.segments[0] != gfa.segments[1]
    assert gfa.paths[0] == gfa.paths[0]
    assert gfa.paths[0] != gfa.paths[1]
    assert gfa.links[0] == gfa.links[0]
    assert gfa.links[0] != gfa.links[1]

    # Including handles, which do not have their own identity.
    assert gfa.links[1].from_ == gfa.links[2].from_
    assert gfa.links[1].from_ != gfa.links[1].to


def test_hash(gfa):
    # The objects are also hashable, so you can put them in dicts and sets.
    d = {
        gfa.segments[0]: "foo",
        gfa.paths[0]: "bar",
        gfa.links[0]: "baz",
        gfa.links[1].from_: "qux",
    }
    assert d[gfa.segments[0]] == "foo"
    assert d[gfa.paths[0]] == "bar"
    assert d[gfa.links[0]] == "baz"
    assert d[gfa.links[1].from_] == "qux"


def test_slice(gfa):
    # The various container types can be sliced to get narrower ranges.
    assert len(gfa.segments[1:3]) == 2
    assert len(gfa.segments[2:]) == len(gfa.segments) - 2
    assert gfa.segments[1:3][0].name == gfa.segments[1].name

    assert len(gfa.paths[1:]) == 1
    assert len(gfa.links[2:100]) == 2

    assert len(list(gfa.paths[:1])) == 1
