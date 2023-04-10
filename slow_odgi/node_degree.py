import sys
import mygfa
import preprocess
from typing import List, Tuple, Dict

def node_degree(graph):
    # The degree of a node is just the cardinality of in_out for that node
    print('\t'.join(["#node.id", "node.degree"]))
    ins, outs = preprocess.in_out_edges(graph)
    for seg in graph.segments.values():
        seg = seg.name
        out_degree = len(outs[mygfa.SegO(seg, True)]) + len(outs[mygfa.SegO(seg, False)])
        in_degree = len(ins[mygfa.SegO(seg, True)]) + len(ins[mygfa.SegO(seg, False)])
        print('\t'.join([seg, str(in_degree + out_degree)]))


if __name__ == "__main__":
    name = sys.stdin
    graph = mygfa.Graph.parse(sys.stdin)
    node_degree(graph)
