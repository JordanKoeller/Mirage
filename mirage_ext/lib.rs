use std::borrow::Borrow;

use numpy::{
  IntoPyArray, PyArray2, PyArray3, PyReadonlyArray1, PyReadonlyArray2, PyReadonlyArray3,
};
use pyo3::prelude::*;

mod kd_tree;
mod kiddo_tree;
mod reducer_fns;

// use kd_tree::KdTree;
use kiddo_tree::KiddoTree;
use reducer_fns::reducer_fns_mod;
// NOTE
// * numpy defaults to np.float64, if you use other type than f64 in Rust
//   you will have to change type in Python before calling the Rust function.

// The name of the module must be the same as the rust package name
#[pymodule]
fn mirage_ext(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
  m.add_class::<KiddoTree>()?;

  #[pyfn(m)]
  fn reduce_lensed_image<'py>(
    py: Python<'py>,
    indices: PyReadonlyArray2<usize>,
    dimensions: PyReadonlyArray1<usize>,
    hit_color: PyReadonlyArray1<u8>,
  ) -> &'py PyArray3<u8> {
    reducer_fns_mod::reduce_lensed_image(
      indices.as_array(),
      dimensions.as_array(),
      hit_color.as_array(),
    )
    .into_pyarray(py)
  }

  #[pyfn(m)]
  fn reduce_magmap<'py>(
    py: Python<'py>,
    tree: PyRef<KiddoTree>,
    query_points: PyReadonlyArray3<f64>,
    radius: f64,
  ) -> &'py PyArray2<usize> {
    reducer_fns_mod::reduce_magmap(tree.borrow(), query_points.as_array(), radius).into_pyarray(py)
  }
  Ok(())
}
