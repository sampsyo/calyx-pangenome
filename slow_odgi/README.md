# `slow-odgi`

### Overview

`slow-odgi` is a reference implementation of [`odgi`](https://github.com/pangenome/odgi). It is written purely in Python, with correctness and clarity as goals and speed as a non-goal. Think of it as a code-ey spec for `odgi` commands.

### Testing

To test `slow-odgi`, we treat `odgi` as an oracle and compare our outputs against theirs. We mostly test against a set of GFA graphs available in the `odgi` repository, and, in a few cases, supplement these with short hand-rolled GFA files of our own.

To run these tests, you will need 
1. `odgi`; see [here](https://github.com/pangenome/odgi). Our tests were run against a built-from-source copy of `odgi` (commit 34f006f).
2. `turnt`; see [here](https://github.com/cucapra/turnt).

With these in place, run `make test-slow-odgi`. The "oracle" files will be generated first, and this will toss up a large number of warnings which can all be ignored. Then the tests will begin to run, and the `ok`/`not-ok` signals there are actually of interest. 

There are a few known points of divergence versus `odgi`:
1. `flip` disgrees against graphs note5.gfa and flip4.gfa.
2. `inject` disagrees against graphs DRB1-3123.gfa and chr6.C4.gfa.


### Explanation of Commands

The remainder of this document will explain, in some detail, the eleven commands that we have implemented. Below we sometimes elide graph information that is inconsequential to the explanation. Unless specified, this is meant to be read as "don't care" and not as absence. 


#### `chop`
Shortens segments' sequences to a given maximum length, while preserving the end-to-end sequence represented by each path.

Given the graph
```
S	1	AAAA
S	2	TTT
S	3	GGGGCCCC
P	x	1+,3+,2+	*
L	1	+	3	+
L	3	+	2	+
```
running `chop` with parameter `3` gives
```
S	1	AAA
S	2	A
S	3	TTT
S	4	GGG
S	5	GCC
S	6	CC
P	x	1+,2+,4+,5+,6+,3+	*
L	1	+	2	+		// new, to bridge the chop of S1
L	2	+	4	+		// renumber old link 1+3+
L	4	+	5	+		// new, to bridge the chop of S3
L	5	+	6	+		// new, to bridge the chop of S3
L	6	+	3	+		// renumber old link 3+2+
```
That is,
1. Segments that had sequences longer than `3` characters have been chopped, repeatedly if needed.
2. All segments have been renumbered.
3. Paths have been adjusted.
4. Old links have been adjusted and new links added (for reasons given in the comments).


#### `crush`
If sequences contain consecutive instances of the placeholder nucleotide `N`, replaces them with a single `N`.

Given the graph
```
S	1	ANNNN
S	2	NNTNN
S	3	NGGGG
```
running `crush` gives
```
S	1	AN
S	2	NTN
S	3	NGGGG
```
Observe that this is entirely intra-segment; we did not treat the end of S2 and the beginning of S3 as a contiguous "run".


#### `degree`
Generates a table summarizing each segment's _node degree_.

Given the graph
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
S	4	CCCC
P	x	1+,3+,4+,3+	*
P	y	1+,3-		*
L	1	+	2	+	0M
L	1	+	3	+	0M
L	1	+	3	-	0M
L	3	-	4	+	0M
L	2	+	4	+	0M
L	3	+	4	+	0M
```
running `degree` gives
```
1	3
2	2
3	4
4	3
```
Where each row has the name of the segment and the segment's degree. This is just a count of how many times a segment's name appears across the graph's links; the direction of traversal is immaterial. Further, it does not matter how many times the segment appears in the paths.


#### `depth`
Generates a table summarizing each segment's _node depth_.

Given the graph
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
S	4	CCCC
P	x	1+,3+,4+,3+	*
P	y	1+,3-		*
L	1	+	2	+	0M
L	1	+	3	+	0M
L	1	+	3	-	0M
L	3	-	4	+	0M
L	2	+	4	+	0M
L	3	+	4	+	0M
```
running `depth` gives
```
1	2	2
2	0	0
3	3	2
4	1	1
```
Where each row has the name of the segment, the segment's _depth_, and the segment's _unique depth_. The depth is a count of how many times a segment's name appears across the graph's paths; the direction of traversal is immaterial. The unique depth is similar but only counts an appearance on one path once. In both cases, it does not matter how many times the segment appears in the links.


#### `flip`
Flips any paths that traverse their steps more in the backward orientation than the forward. 

Given the graph
```
S	1	A
S	2	TTT
S	3	G
P	x	1+,2-,3+	*
P	y	1+,2+	*
L	1	+	2	+	0M
L	1	+	2	-	0M
L	2	+	3	+	0M
```
running `flip` gives 
```
S	1	A
S	2	TTT
S	3	G
P	x_inv	3-,2+,1-	*			// changed in place
P	y	1+,2+	*
L	1	+	2	+	0M
L	1	+	2	-	0M
L	2	+	1	-	0M		// new
L	2	+	3	+	0M
L	3	-	2	+	0M		// new

```
That is, 
1. Any paths that were stepping more backwards than forwards have been flipped. Note that this is _weighted_ by sequence length, which is why the single `2-` in path `x` is enough to justify flipping path `x`. The flipping involves flipping the sign of each step the path traverses and also reversing the path's list of steps.
2. Those paths that have just been fllipped have had `_inv` added to their names.
3. Links have been added in support of the newly flipped paths.


#### `flatten`
Converts the graph into an alternate representation, represented by a FASTA and a BED. The new representation loses link information but retains path information.

Given the graph
```
S	1	AAAA
S	2	TT
S	3	GGGG
P	x	1+,2+,3+	*
P	y	3+,2-
```
running `flatten` produces two outputs:
```
AAAATTGGGG
```
and
```
0	4	x	+	0
4	6	x	+	1
6	10	x	+	2
6	10	y	+	0
4	6	y	-	1
```
That is, 
1. In the first file, just a concatenation of all the segments' sequences. This is called the FASTA file.
2. In the second file, a "key" by which to retrieve path information from the FASTA file. This file is called the BED file, and each of its rows is read as follows:
	- The name in the middle tells us which path we are describing.
	- The number on the far right says which segment of the path we are describing.
	- The two numbers of the left say where to start and stop reading off the FASTA file.
	- The fourth item, the sign, says whether the path crossed that sequence in the forwards or backwards direction.


#### `inject`
Adds new paths, as specified, to the graph. The paths must be subpaths of existing paths.

Given the graph
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
P	x	1+,2+,3+	*
```
and a BED file
```
x	0	8	y 
x	0	4	z
```
running `inject` gives
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
P	x	1+,2+,3+	*
P	y	1+,2+	*		// new
P	z	1+	*		// new
```
That is, the BED file has information about which paths to track and, for each path, over which of its run to track it and what name to give the resultant subpath. Running `inject` adds these paths.

Consider, though, a more subtle example. The following BED file describes a legal subpath, but one that does not happen to line up with the current segment-boundaries.
```
x	1	6	y    
```
Working with the original graph and this new BED file, `inject` now needs to split segments 1  and 2 in order to add path `y`.
```
S	1	A
S	2	AAA
S	3	TT
S	4	TT
S	5	GGGG
P	x	1+,2+,3+,4+,5+	*	// changed in place
P	y	2+,3+	*		// new
```
Observe that this required edits to the path `x` as well.   


#### `matrix`
Represents the graph as a matrix. While this retains link information, it loses path information.

Given the graph
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
S	4	CCCC
L	1	+	2	+	0M
L	1	+	3	+	0M
L	1	+	3	-	0M
```
running `matrix` produces 
```
4	4	12		// header
1	2	1
2	1	1
1	3	1
3	1	1
1	3	1
3	1	1
1	2	1
2	1	1
2	4	1
4	2	1
3	4	1
4	3	1
```
That is, 
1. A _header_ that twice lists the highest-numbered segment, and then lists the total number of entries in the matrix below.
2. Rows that indicate adjacency. Each row ends with `1`. Observe, further:
	- Each link triggers two adjacencies; e.g., the presence of `L 1 + 2 +` was enough to add both `1 2` and `2 1` to the matrix.
	- The direction of link traversal did not matter; the fact that `L 1 + 3 -` pointed at the "reverse" handle of segment 3 did not have any effect in the matrix representation.
	- No deduplication was performed.


#### `normalize`
Runs a normalization pass over the graph.

GFAs have line-entries of four kinds: headers, segments, paths, and links. Their order does not matter, so the following is fine:
```
H	...
L	...
P	...
S	...
L	...
P	...
S	...
```
This command normalizes a GFA so that its entries appear in a stable order: headers, then segments, then paths, and then links. Order is also enforced between lines of the same kind. Doing this minimizes diffs when modifying files. 


#### `overlap`
Queries the graph about which paths overlap with which other paths.

Given the graph
```
S	1	AAAA...	// a sequence of length 90
S	2	TTTT...	// a sequence of length 10
S	3	GGGG...	// a sequence of length 40
P	x	1+,2+	*
P	y	2+,3+	*
P	z	1+
```
and the BED file
```
x	0	30
```
running `overlap` gives nothing: no paths in the graph overlapped with path `x` between its 0th and 30th characters.

As one would expect, running the same graph with the BED file
```
x	95	97       
```
gives the answer
```
x	95	97	y
```
which says that the path `y` overlapped with path `x` between the 95th and 97th indices.

It is also possible to query `overlap` with a simpler file of the form
```
y
```
and, in this case, `overlap` assumes that the querier wants to investigate the path `y` along its entire length. The answer is
```
y	0	50	x
```


#### `paths`
Lists the paths of the graph.

Given the graph
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
P	x	1+,2+,3+	*
P	y	2+,3+
```
running `paths` gives
```
x
y
```


#### `validate`
Checks whether the links of the graph are in agreement with the steps that the paths of the graph describe.

Given the graph
```
S	1	AAAA
S	2	TTTT
S	3	GGGG
P	x	1+,2+,3+	*
L	1	+	2	+
L	3	+	1	-
// no more links
```
running `validate` complains that we are missing a link; namely the link `L 2 + 3 +`. It does not complain about the "extra" link `3 + 1 -`. If run against a graph where each path _is_ backed up by links, this command decrees the graph valid and succeeds quietly.