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
    pub overlaps: Range<usize>,
}

#[derive(Debug)]
pub struct LinkInfo {
    pub from: Handle,
    pub to: Handle,
    pub overlap: Range<usize>,
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

#[derive(Debug)]
#[repr(transparent)]
pub struct Alignment<'a> {
    pub ops: &'a [AlignOp],
}

#[derive(Debug, Default)]
pub struct FlatGFA {
    pub header: Option<BString>,
    pub segs: Vec<SegInfo>,
    pub paths: Vec<PathInfo>,
    pub links: Vec<LinkInfo>,

    pub steps: Vec<Handle>,
    pub seqdata: Vec<u8>,
    pub overlaps: Vec<Range<usize>>,
    pub alignment: Vec<AlignOp>,
}

impl FlatGFA {
    pub fn get_seq(&self, seg: &SegInfo) -> &BStr {
        self.seqdata[seg.seq.clone()].as_ref()
    }

    pub fn get_steps(&self, path: &PathInfo) -> &[Handle] {
        &self.steps[path.steps.clone()]
    }

    pub fn get_overlaps(&self, path: &PathInfo) -> &[Range<usize>] {
        &self.overlaps[path.overlaps.clone()]
    }

    pub fn get_alignment(&self, overlap: &Range<usize>) -> Alignment {
        Alignment {
            ops: &self.alignment[overlap.clone()],
        }
    }

    pub fn add_header(&mut self, version: Vec<u8>) {
        assert!(self.header.is_none());
        self.header = Some(version.into());
    }

    pub fn add_seg(&mut self, name: usize, seq: Vec<u8>) -> usize {
        pool_push(
            &mut self.segs,
            SegInfo {
                name,
                seq: pool_append(&mut self.seqdata, seq),
            },
        )
    }

    pub fn add_path(
        &mut self,
        name: Vec<u8>,
        steps: Vec<Handle>,
        overlaps: Vec<Vec<AlignOp>>,
    ) -> usize {
        let path_id = pool_push(
            &mut self.paths,
            PathInfo {
                name: BString::new(name),
                steps: pool_append(&mut self.steps, steps),
                overlaps: Range {
                    start: self.overlaps.len(),
                    end: self.overlaps.len() + overlaps.len(),
                },
            },
        );

        for align in overlaps {
            self.overlaps.push(pool_append(&mut self.alignment, align));
        }

        path_id
    }

    pub fn add_link(&mut self, from: Handle, to: Handle, overlap: Vec<AlignOp>) -> usize {
        pool_push(
            &mut self.links,
            LinkInfo {
                from,
                to,
                overlap: pool_append(&mut self.alignment, overlap),
            },
        )
    }
}

/// Add an item to a "pool" vector and get the new index (ID).
fn pool_push<T>(vec: &mut Vec<T>, item: T) -> usize {
    let len = vec.len();
    vec.push(item);
    len
}

/// Add an entire collection of items to a "pool" vector and return the
/// range of new indices (IDs).
fn pool_append<T>(vec: &mut Vec<T>, items: Vec<T>) -> Range<usize> {
    let range = vec.len()..(vec.len() + items.len());
    vec.extend(items);
    range
}
