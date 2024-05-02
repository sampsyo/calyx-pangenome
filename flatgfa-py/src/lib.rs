use flatgfa::flatgfa::{FlatGFA, GFABuilder, HeapStore};
use pyo3::prelude::*;
use pyo3::types::PyBytes;

#[pyfunction]
fn parse(filename: &str) -> PyFlatGFA {
    let file = flatgfa::file::map_file(filename);
    let store = flatgfa::parse::Parser::for_heap().parse_mem(file.as_ref());
    PyFlatGFA(store)
}

#[pyclass(frozen)]
#[pyo3(name = "FlatGFA")]
struct PyFlatGFA(HeapStore);

#[pymethods]
impl PyFlatGFA {
    #[getter]
    fn segments(self_: Py<Self>) -> SegmentList {
        SegmentList { gfa: GFARef(self_) }
    }
}

#[derive(Clone)]
struct GFARef(Py<PyFlatGFA>);

impl GFARef {
    fn view(&self) -> FlatGFA {
        self.0.get().0.view()
    }
}

#[pyclass]
struct SegmentList {
    gfa: GFARef,
}

#[pymethods]
impl SegmentList {
    fn __getitem__<'py>(&self, idx: u32) -> PySegment {
        PySegment {
            gfa: self.gfa.clone(),
            id: idx,
        }
    }

    fn __iter__(&self) -> SegmentIter {
        SegmentIter {
            gfa: self.gfa.clone(),
            idx: 0,
        }
    }
}

#[pyclass]
struct SegmentIter {
    gfa: GFARef,
    idx: u32,
}

#[pymethods]
impl SegmentIter {
    fn __iter__(self_: Py<Self>) -> Py<Self> {
        self_
    }

    fn __next__<'py>(&mut self) -> Option<PySegment> {
        let view = self.gfa.view();
        if self.idx < view.segs.len() as u32 {
            let seg = PySegment {
                gfa: self.gfa.clone(),
                id: self.idx,
            };
            self.idx += 1;
            Some(seg)
        } else {
            None
        }
    }
}

#[pyclass(frozen)]
#[pyo3(name = "Segment")]
struct PySegment {
    gfa: GFARef,
    #[pyo3(get)]
    id: u32,
}

#[pymethods]
impl PySegment {
    fn sequence<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        let view = self.gfa.view();
        let seg = view.segs[self.id as usize];
        let seq = view.get_seq(&seg);
        PyBytes::new_bound(py, seq) // TK Can we avoid this copy?
    }

    #[getter]
    fn name<'py>(&self) -> usize {
        let view = self.gfa.view();
        let seg = view.segs[self.id as usize];
        seg.name
    }

    fn __repr__(&self) -> String {
        format!("<Segment {}>", self.id)
    }
}

#[pymodule]
#[pyo3(name = "flatgfa")]
fn pymod(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(parse, m)?)?;
    Ok(())
}
