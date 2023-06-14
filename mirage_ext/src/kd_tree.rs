use std::cmp::{Ord, Ordering, Reverse};
use std::collections::{BinaryHeap, VecDeque};

use ndarray::{self, arr1, Axis};
use numpy::{IntoPyArray, PyArray1, PyReadonlyArray2, PyReadonlyArrayDyn};
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
  pub fn new_py<'py>(data: PyReadonlyArray2<'py, f64>, node_size: usize) -> Self {
    Self {
      data: data.to_owned_array(),
      indices: ndarray::Array1::from_iter(0..data.shape()[0]),
      node_size,
      partition_tree: Vec::new(),
    }
    .init_tree()
  }

  fn query_near<'py>(
    &self,
    python: Python<'py>,
    x: f64,
    y: f64,
    radius: f64,
  ) -> &'py PyArray1<usize> {
    println!("Query_near_rs");
    let ret = python.allow_threads(|| self.query_near_rs(x, y, radius));
    println!("Done Query_near_rs");
    ret.into_pyarray(python)
  }

  fn query_near_count<'py>(&self, x: f64, y: f64, radius: f64) -> usize {
    println!("Query_near_count_rs");
    let ret = self.query_near_count_rs(x, y, radius);
    println!("Done Query_near_count_rs");
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
    println!("Start init tree");
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
    println!("End init tree");
    self
  }

  fn partition(&mut self, start_i: usize, end_i: usize, d: usize) -> f64 {
    // Todo: Optimize this another time. I'm just going to heapsort
    let mut heap = BinaryHeap::new();
    let k = (start_i + end_i) / 2;
    for i in start_i..end_i {
      heap.push(Reverse(SortIndexArrayElem::new(self.data.view(), i, d)));
    }
    let mut ret = self.data[[self.indices[start_i], d]];
    for i in start_i..end_i {
      let elem = heap.pop().unwrap().0;
      self.indices[i] = elem.index;
      if elem.index == k {
        ret = elem.value();
      }
    }
    ret
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

struct SortIndexArrayElem<'a> {
  pub index: usize,
  data: ndarray::ArrayView2<'a, f64>,
  dimension: usize,
}

impl<'a> SortIndexArrayElem<'a> {
  fn new(data: ndarray::ArrayView2<'a, f64>, index: usize, dimension: usize) -> Self {
    Self {
      data,
      index,
      dimension,
    }
  }

  fn value(&self) -> f64 {
    self.data[[self.index, self.dimension]]
  }
}

impl<'a> PartialEq for SortIndexArrayElem<'a> {
  fn eq(&self, other: &Self) -> bool {
    self.value() == other.value()
  }
}

impl<'a> PartialOrd for SortIndexArrayElem<'a> {
  fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
    self.value().partial_cmp(&other.value())
  }
}

impl<'a> Ord for SortIndexArrayElem<'a> {
  fn cmp(&self, other: &Self) -> Ordering {
    let lhs = self.value();
    let rhs = other.value();
    if lhs < rhs {
      Ordering::Less
    } else if lhs == rhs {
      Ordering::Equal
    } else {
      Ordering::Greater
    }
  }
}

impl<'a> Eq for SortIndexArrayElem<'a> {}
