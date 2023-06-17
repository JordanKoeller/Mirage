use numpy::{PyArray3, PyReadonlyArray1, PyReadonlyArray2, IntoPyArray};
use pyo3::prelude::{pymodule, PyModule, PyResult, Python};

mod kd_tree;
mod reducer_fns;

use kd_tree::KdTree;
use reducer_fns::reducer_fns_mod;
// NOTE
// * numpy defaults to np.float64, if you use other type than f64 in Rust
//   you will have to change type in Python before calling the Rust function.

// The name of the module must be the same as the rust package name
#[pymodule]
fn mirage_ext(_py: Python<'_>, m: &PyModule) -> PyResult<()> {
  m.add_class::<KdTree>()?;

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
  // This is a pure function (no mutations of incoming data).
  // You can see this as the python array in the function arguments is readonly.
  // The object we return will need ot have the same lifetime as the Python.
  // Python will handle the objects deallocation.
  // We are having the Python as input with a lifetime parameter.
  // Basically, none of the data that comes from Python can survive
  // longer than Python itself. Therefore, if Python is dropped, so must our Rust Python-dependent variables.
  // #[pyfn(m)]
  // fn max_min<'py>(py: Python<'py>, x: PyReadonlyArrayDyn<f64>) -> &'py PyArray1<f64> {
  //     // Here we have a numpy array of dynamic size. But we could restrict the
  //     // function to only take arrays of certain size
  //     // e.g. We could say PyReadonlyArray3 and only take 3 dim arrays.
  //     // These functions will also do type checking so a
  //     // numpy array of type np.float32 will not be accepted and will
  //     // yield an Exception in Python as expected
  //     let array = x.as_array();
  //     let result_array = rust_fn::max_min(&array);
  //     result_array.into_pyarray(py)
  // }
  // #[pyfn(m)]
  // fn double_and_random_perturbation(
  //     _py: Python<'_>,
  //     x: &PyArrayDyn<f64>,
  //     perturbation_scaling: f64,
  // ) {
  //     // First we convert the Python numpy array into Rust ndarray
  //     // Here, you can specify different array sizes and types.
  //     let mut array = unsafe { x.as_array_mut() }; // Convert to ndarray type

  //     // Mutate the data
  //     // No need to return any value as the input data is mutated
  //     rust_fn::double_and_random_perturbation(&mut array, perturbation_scaling);
  // }

  // #[pyfn(m)]
  // fn eye<'py>(py: Python<'py>, size: usize) -> &PyArray2<f64> {
  //     // Simple demonstration of creating an ndarray inside Rust and return
  //     let array = ndarray::Array::eye(size);
  //     array.into_pyarray(py)
  // }

  Ok(())
}

mod mirage_fn {}
