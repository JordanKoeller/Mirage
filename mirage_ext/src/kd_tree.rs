use std::collections::{VecDeque};

use ndarray::arr1;
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray2};
use pyo3::prelude::*;

#[pyclass]
pub struct KdTree {
  data: ndarray::Array2<f64>,
  indices: ndarray::Array1<usize>,
  node_size: usize,
  partition_tree: Vec<KdTreeNode>,
}

#[pymethods]
impl KdTree {
  #[new]
  pub fn new_py<'py>(
    python: Python<'py>,
    data: PyReadonlyArray2<'py, f64>,
    node_size: usize,
  ) -> Self {
    let owned_array = data.to_owned_array();
    python.allow_threads(move || {
      Self {
        indices: ndarray::Array1::from_iter(0..owned_array.shape()[0]),
        data: owned_array,
        node_size,
        partition_tree: Vec::new(),
      }
      .init_tree()
    })
  }

  fn query_near<'py>(
    &self,
    python: Python<'py>,
    x: f64,
    y: f64,
    radius: f64,
  ) -> &'py PyArray1<usize> {
    let ret = python.allow_threads(|| self.query_near_rs(x, y, radius));
    ret.into_pyarray(python)
  }

  fn query_near_count<'py>(&self, x: f64, y: f64, radius: f64) -> usize {
    let ret = self.query_near_count_rs(x, y, radius);
    ret
  }
}

impl KdTree {
  pub fn new(data: ndarray::Array2<f64>, node_size: usize) -> Self {
    Self {
      indices: ndarray::Array1::from_iter(0..data.shape()[0]),
      data,
      node_size,
      partition_tree: Vec::new(),
    }
    .init_tree()
  }

  fn query_near_rs(&self, x: f64, y: f64, radius: f64) -> ndarray::Array1<usize> {
    let mut vertices = Vec::new();
    self.kd_reduce(ndarray::arr1(&[x, y]), radius, |ind| vertices.push(ind));
    arr1(&vertices)
  }

  fn query_near_count_rs(&self, x: f64, y: f64, radius: f64) -> usize {
    let mut count = 0usize;
    self.kd_reduce(ndarray::arr1(&[x, y]), radius, |_ind| count += 1);
    count
  }

  // Helper functions below
  fn kd_reduce<R: FnMut(usize) -> ()>(
    &self,
    position: ndarray::Array1<f64>,
    radius: f64,
    mut reducer: R,
  ) {
    let mut nodes = vec![0];
    let r2 = radius * radius;
    while nodes.len() > 0 {
      let node_ind = nodes.pop().unwrap();
      let node = &self.partition_tree[node_ind];
      let left_child = node_ind * 2 + 1;
      let right_child = node_ind * 2 + 2;
      if left_child < nodes.len() && node.partition_value >= position[node.dimension] - radius {
        // Need to recurse down left
        nodes.push(left_child);
      }
      if right_child < nodes.len() && node.partition_value <= position[node.dimension] + radius {
        // Need to recurse down right
        nodes.push(right_child);
      }
      if nodes.len() < left_child {
        // We are at a leaf. So time to accumulate!
        for i in node.start_index..node.end_index {
          let elem_pos = ndarray::arr1(&[
            self.data[[self.indices[i], 0usize]],
            self.data[[self.indices[i], 1usize]],
          ]);
          let delta = elem_pos - &position;
          if delta.dot(&delta) < r2 {
            reducer(self.indices[i]);
          }
        }
      }
    }
  }

  fn init_tree(mut self) -> Self {
    let mut splits_queue = VecDeque::new();
    splits_queue.push_back(KdTreeNode::new(0, self.data.shape()[0], 0));
    while splits_queue.len() > 0 {
      let mut node = splits_queue.pop_front().unwrap();
      if node.end_index - node.start_index > self.node_size {
        let midpt = self.partition(node.start_index, node.end_index, node.dimension);
        node.partition_value = midpt;
        let dim = (node.dimension + 1) % 2;
        let mid_index = (node.end_index + node.start_index) / 2;
        splits_queue.push_back(KdTreeNode::new(node.start_index, mid_index, dim));
        splits_queue.push_back(KdTreeNode::new(mid_index, node.end_index, dim));
      }
      self.partition_tree.push(node);
    }
    self
  }

  fn partition(&mut self, start_i: usize, end_i: usize, d: usize) -> f64 {
    // Todo: Optimize this another time. I'm just going to heapsort
    let k = (start_i + end_i) / 2 - start_i;
    let mut sort_vec = Vec::from_iter(start_i..end_i);
    sort_vec.sort_unstable_by(|&i, &j| {
      let i_v: f64 = self.data[[i, d]];
      let j_v: f64 = self.data[[j, d]];
      i_v.total_cmp(&j_v)
    });
    for i in start_i..end_i {
      self.indices[i] = sort_vec[i - start_i];
    }
    self.data[[sort_vec[k], d]]
  }
}

// Inclusive on the low end, exclusive on the high
struct KdTreeNode {
  pub start_index: usize,
  pub end_index: usize,
  pub partition_value: f64,
  pub dimension: usize,
}

impl KdTreeNode {
  pub fn new(s: usize, e: usize, dimension: usize) -> Self {
    Self {
      start_index: s,
      end_index: e,
      partition_value: 0f64,
      dimension,
    }
  }
}
