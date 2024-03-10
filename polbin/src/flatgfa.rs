use bstr::{BStr, BString};
use std::ops::Range;

#[derive(Debug)]
pub struct SegInfo {
    pub name: usize,
    pub seq: Range<usize>,
}

#[derive(Debug)]
pub struct PathInfo {
    pub name: BString,
    pub steps: Range<usize>,
    pub alignment: Range<usize>,
}

#[derive(Debug)]
pub struct LinkInfo {
    pub from: Handle,
    pub to: Handle,
}

#[derive(Debug, PartialEq)]
pub enum Orientation {
    Forward,
    Backward,
}

#[derive(Debug, PartialEq)]
pub struct Handle {
    pub segment: usize,
    pub orient: Orientation,
}

#[derive(Debug)]
pub enum AlignOpcode {
    Match,     // M
    Gap,       // N
    Insertion, // D
    Deletion,  // I
}

#[derive(Debug)]
pub struct AlignOp {
    pub op: AlignOpcode,
    pub len: u32,
}

#[derive(Debug, Default)]
pub struct FlatGFA {
    pub header: Option<BString>,
    pub segs: Vec<SegInfo>,
    pub paths: Vec<PathInfo>,
    pub links: Vec<LinkInfo>,

    pub steps: Vec<Handle>,
    pub seqdata: Vec<u8>,
    pub align_chunks: Vec<Range<usize>>,
    pub alignment: Vec<AlignOp>,
}

impl FlatGFA {
    pub fn get_seq(&self, seg: &SegInfo) -> &BStr {
        self.seqdata[seg.seq.clone()].as_ref()
    }

    pub fn get_steps(&self, path: &PathInfo) -> &[Handle] {
        &self.steps[path.steps.clone()]
    }

    pub fn add_header(&mut self, version: Vec<u8>) {
        assert!(self.header.is_none());
        self.header = Some(version.into());
    }

    pub fn add_seg(&mut self, name: usize, seq: Vec<u8>) -> usize {
        self.segs.push(SegInfo {
            name,
            seq: Range {
                start: self.seqdata.len(),
                end: self.seqdata.len() + seq.len(),
            },
        });
        self.seqdata.extend(seq);
        self.segs.len() - 1
    }

    pub fn add_path(
        &mut self,
        name: Vec<u8>,
        steps: Vec<Handle>,
        overlaps: Vec<Vec<AlignOp>>,
    ) -> usize {
        self.paths.push(PathInfo {
            name: BString::new(name),
            steps: Range {
                start: self.steps.len(),
                end: self.steps.len() + steps.len(),
            },
            alignment: Range {
                start: self.align_chunks.len(),
                end: self.align_chunks.len() + overlaps.len(),
            },
        });
        self.steps.extend(steps);

        for align in overlaps {
            self.align_chunks.push(Range {
                start: self.alignment.len(),
                end: self.alignment.len() + align.len(),
            });
            self.alignment.extend(align);
        }

        self.paths.len() - 1
    }

    pub fn add_link(&mut self, from: Handle, to: Handle) -> usize {
        self.links.push(LinkInfo { from, to });
        self.links.len() - 1
    }
}
