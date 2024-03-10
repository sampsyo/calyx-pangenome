use bstr::{BStr, BString};
use std::ops::Range;

#[derive(Debug)]
pub struct Segment {
    pub name: usize,
    pub seq: Range<usize>,
    pub optional: Range<usize>,
}

#[derive(Debug)]
pub struct Path {
    pub name: Range<usize>,
    pub steps: Range<usize>,
    pub overlaps: Range<usize>,
}

#[derive(Debug)]
pub struct Link {
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

#[derive(Debug)]
pub enum LineKind {
    Header,
    Segment,
    Path,
    Link,
}

#[derive(Debug, Default)]
pub struct FlatGFA {
    pub header: Option<BString>,
    pub segs: Vec<Segment>,
    pub paths: Vec<Path>,
    pub links: Vec<Link>,

    pub steps: Vec<Handle>,
    pub seqdata: Vec<u8>,
    pub overlaps: Vec<Range<usize>>,
    pub alignment: Vec<AlignOp>,
    pub namedata: BString,
    pub optional_data: BString,

    pub line_order: Vec<LineKind>,
}

impl FlatGFA {
    pub fn get_seq(&self, seg: &Segment) -> &BStr {
        self.seqdata[seg.seq.clone()].as_ref()
    }

    pub fn get_steps(&self, path: &Path) -> &[Handle] {
        &self.steps[path.steps.clone()]
    }

    pub fn get_overlaps(&self, path: &Path) -> &[Range<usize>] {
        &self.overlaps[path.overlaps.clone()]
    }

    pub fn get_path_name(&self, path: &Path) -> &BStr {
        self.namedata[path.name.clone()].as_ref()
    }

    pub fn get_optional_data(&self, seg: &Segment) -> &BStr {
        self.optional_data[seg.optional.clone()].as_ref()
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

    pub fn add_seg(&mut self, name: usize, seq: Vec<u8>, optional: Vec<u8>) -> usize {
        pool_push(
            &mut self.segs,
            Segment {
                name,
                seq: pool_append(&mut self.seqdata, seq),
                optional: pool_append(&mut self.optional_data, optional),
            },
        )
    }

    pub fn add_path(
        &mut self,
        name: Vec<u8>,
        steps: Vec<Handle>,
        overlaps: Vec<Vec<AlignOp>>,
    ) -> usize {
        let overlap_count = overlaps.len();
        let overlaps = pool_extend(
            &mut self.overlaps,
            overlaps
                .into_iter()
                .map(|align| pool_append(&mut self.alignment, align)),
            overlap_count,
        );

        pool_push(
            &mut self.paths,
            Path {
                name: pool_append(&mut self.namedata, name),
                steps: pool_append(&mut self.steps, steps),
                overlaps,
            },
        )
    }

    pub fn add_link(&mut self, from: Handle, to: Handle, overlap: Vec<AlignOp>) -> usize {
        pool_push(
            &mut self.links,
            Link {
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

/// Add an entire vector of items to a "pool" vector and return the
/// range of new indices (IDs).
fn pool_append<T>(vec: &mut Vec<T>, items: Vec<T>) -> Range<usize> {
    let count = items.len();
    pool_extend(vec, items, count)
}

/// Like `pool_append`, for an iterator. It's pretty important that `count`
/// actually be the number of items in the iterator!
fn pool_extend<T>(
    vec: &mut Vec<T>,
    iter: impl IntoIterator<Item = T>,
    count: usize,
) -> Range<usize> {
    let range = vec.len()..(vec.len() + count);
    let old_len = vec.len();
    vec.extend(iter);
    assert_eq!(vec.len(), old_len + count);
    range
}
