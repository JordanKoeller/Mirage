use bincode::{deserialize, serialize};
use kiddo::float::distance::squared_euclidean;
use kiddo::float::kdtree::KdTree;
use kiddo::float::neighbour::Neighbour;
use numpy::{PyArray2, ToPyArray};
use numpy::{PyArray3, PyReadonlyArray3};
use pyo3::prelude::*;
use pyo3::types::PyBytes;
use serde::{Deserialize, Serialize};
// use numpy::{ToPyArray, PyArray};

#[pyclass(module = "mirage_ext")]
pub struct KiddoTree {
  tree: kiddo::KdTree<f64, 2>,
  dataset: ndarray::Array3<f64>,
}

#[pymethods]
impl KiddoTree {
  #[new]
  pub fn new_py<'py>(python: Python<'py>, data: PyReadonlyArray3<'py, f64>) -> Self {
    let owned = data.to_owned_array();
    python.allow_threads(move || Self::new(owned))
  }

  pub fn query_count<'py>(&self, python: Python<'py>, x: f64, y: f64, radius: f64) -> usize {
    python.allow_threads(|| self.query_count_rs(x, y, radius))
  }

  /**
   *
   */
  pub fn query_indices<'py>(
    &self,
    python: Python<'py>,
    x: f64,
    y: f64,
    radius: f64,
  ) -> &'py PyArray2<usize> {
    python
      .allow_threads(|| self.query_indices_rs(x, y, radius))
      .to_pyarray(python)
  }

  pub fn query_rays<'py>(
    &self,
    python: Python<'py>,
    x: f64,
    y: f64,
    radius: f64,
  ) -> &'py PyArray2<f64> {
    python
      .allow_threads(|| self.query_rays_rs(x, y, radius))
      .to_pyarray(python)
  }

  pub fn __setstate__(&mut self, state: &PyBytes) -> PyResult<()> {
    *self = deserialize(state.as_bytes()).unwrap();
    Ok(())
  }
  pub fn __getstate__<'py>(&self, py: Python<'py>) -> PyResult<&'py PyBytes> {
    Ok(PyBytes::new(py, &serialize(&self).unwrap()))
  }
  pub fn __getnewargs__<'py>(&self, py: Python<'py>) -> PyResult<(&'py PyArray3<f64>,)> {
    Ok((self.dataset.to_pyarray(py), ))
  }
}

impl KiddoTree {
  fn new(dataset: ndarray::Array3<f64>) -> Self {
    let mut tree = KdTree::new();
    for i in 0..dataset.shape()[0] {
      for j in 0..dataset.shape()[1] {
        let pt: [f64; 2] = [
          *dataset.get((i, j, 0)).unwrap(),
          *dataset.get((i, j, 1)).unwrap(),
        ];
        tree.add(&pt, i);
      }
    }
    KiddoTree { tree, dataset }
  }

  pub fn query_count_rs(&self, x: f64, y: f64, radius: f64) -> usize {
    self.query_helper(x, y, radius).len()
  }

  pub fn query_indices_rs(&self, x: f64, y: f64, radius: f64) -> ndarray::Array2<usize> {
    let neighbors = self.query_helper(x, y, radius);

    ndarray::Array2::from_shape_fn((neighbors.len(), 2), |(i, j)| {
      if j == 0 {
        neighbors[i].item / self.dataset.shape()[1]
      } else {
        neighbors[i].item % self.dataset.shape()[1]
      }
    })
  }

  pub fn query_rays_rs(&self, x: f64, y: f64, radius: f64) -> ndarray::Array2<f64> {
    let neighbors = self.query_helper(x, y, radius);

    ndarray::Array2::from_shape_fn((neighbors.len(), self.dataset.shape()[2]), |(i, j)| {
      let flat_index = neighbors[i].item;
      let x = flat_index / self.dataset.shape()[1];
      let y = flat_index % self.dataset.shape()[0];
      *self.dataset.get((x, y, j)).unwrap()
    })
  }

  fn query_helper(&self, x: f64, y: f64, radius: f64) -> Vec<Neighbour<f64, usize>> {
    self
      .tree
      .within_unsorted(&[x, y], radius, &squared_euclidean)
  }
}

impl<'de> Deserialize<'de> for KiddoTree {
  fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
  where
    D: serde::Deserializer<'de>,
  {
    let dataset = ndarray::Array3::<f64>::deserialize(deserializer)?;
    Ok(KiddoTree::new(dataset))
  }
}

impl Serialize for KiddoTree {
  fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
  where
    S: serde::Serializer,
  {
    self.dataset.serialize(serializer)
  }
}

#[cfg(test)]
mod test {
  use super::KiddoTree;

  #[test]
  fn kiddoTree_constructs() {
    get_tree(10, 10);
  }

  #[test]
  fn queryCount_success() {
    let tree = get_tree(50, 50);
    let radius = 0.2;
    let pt = [0.1, 0.4];

    let actual = tree.query_count_rs(pt[0], pt[1], radius);

    let expected = bf_indices_within(&tree.dataset, radius, pt);

    assert_eq!(expected.len(), actual);
  }

  fn get_tree(i: usize, j: usize) -> KiddoTree {
    let mut data = ndarray::Array3::ones((i, j, 2));

    for x in 0..i {
      for y in 0..j {
        data[(x, y, 0)] = ((x * y + x) as f64).sin() * 10f64; // Pseudo-random
        data[(x, y, 1)] = ((y * x + y) as f64).cos() * 10f64; // Pseudo-random
      }
    }

    KiddoTree::new(data)
  }

  fn bf_indices_within(data: &ndarray::Array3<f64>, radius: f64, pt: [f64; 2]) -> Vec<[usize; 2]> {
    let r2 = radius * radius;
    let mut indices: Vec<[usize; 2]> = Vec::new();
    for i in 0..data.shape()[0] {
      for j in 0..data.shape()[1] {
        let dx = data.get((i, j, 0)).unwrap() - pt[0];
        let dy = data.get((i, j, 1)).unwrap() - pt[1];
        if dx * dx + dy * dy < r2 {
          indices.push([i, j]);
        }
      }
    }
    indices
  }
}
