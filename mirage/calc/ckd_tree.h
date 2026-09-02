#ifndef MIRAGE_CALC_CKD_TREE_H_
#define MIRAGE_CALC_CKD_TREE_H_

#include <functional>
#include <iostream>
#include <queue>
#include <vector>

// A header-only KD-Tree, hyper-optimized for the Mirage usecase.
//
// Most notably, this is not a "real" KD-Tree that is K-dimensional. It is
// specific for Mirage, which only requires support for two dimensions.
//
// Additionally, this class does not take ownership of the passed-in data,
// and mutates it inplace.
//
//
// Potential future optimizations:
// + Explore columnar vs row-wise storage tradeoffs.
// + Store bounding boxes foreach node to allow for quick exclusion of dead
//   zones without needing recursion
class CKDTree {
public:
  // Construct a CKDTree.
  //
  // Args:
  //   buf: Pointer to the front of the buffer containing coordinates in
  //   columnar order. sz: Number of elements in buf. elem_sz: The number of
  //   floats per element (in columnar order). leaf_size: The number of elements
  //   to include in each leaf node.

  static CKDTree Create(double *buf, size_t sz, long *indices, double *splits,
                        size_t elem_sz, size_t leaf_size) {
    return CKDTree(buf, sz, indices, splits, elem_sz, leaf_size, false);
  }

  static CKDTree CreatePreconstructed(double *buf, size_t sz, long *indices,
                                      double *splits, size_t elem_sz,
                                      size_t leaf_size) {
    return CKDTree(buf, sz, indices, splits, elem_sz, leaf_size, true);
  }

  CKDTree() {}

  // Return the number of elements in the tree that are within the circle of
  // radius r at location (cx, cy).
  size_t PointsInCircle(double cx, double cy, double r) {
    size_t count = 0;
    std::function<void(size_t)> reducer([&](size_t i) -> void { count++; });
    Reduce(cx, cy, r, &reducer);
    return count;
  }

  // batch version of PointsInCircle. Queries sz many circles, with centers
  // specified in row-order.
  void PointsInCircle(double *centers, size_t sz, double r, double *out) {
    for (size_t i = 0; i < sz; i++) {
      out[i] = (double)PointsInCircle(centers[2 * i], centers[2 * i + 1], r);
    }
  }

  // Return the magnification coefficient for the specified circle of radius
  // r at location (cx, cy).
  //
  // If the tree does not contain magnification data 0 is returned.
  double MagnificationCoefficient(double cx, double cy, double r) {
    if (elem_sz_ == 2) {
      return 0.0;
    }
    // Using Kahan summation algorithm to avoid numerical instability
    // https://en.wikipedia.org/wiki/Kahan_summation_algorithm
    double sum, c, y, t;
    sum = 0.0;
    c = 0.0;
    std::function<void(size_t)> reducer([&](size_t i) -> void {
      y = buf_[sz_ * 2 + i] - c;
      t = sum + y;
      c = (t - sum) - y;
      sum = t;
    });
    Reduce(cx, cy, r, &reducer);
    return sum;
  }

  // batch version of MagnificationCoefficient. Queries sz many circles, with
  // centers specified in row-order.
  void MagnificationCoefficient(double *centers, size_t sz, double r,
                                double *out) {
    for (size_t i = 0; i < sz; i++) {
      out[i] = MagnificationCoefficient(centers[2 * i], centers[2 * i + 1], r);
    }
  }

  // Returns the indices of the rays within the specified circle.
  //
  // Indices are returned as a flattened value.
  std::vector<long> LensPlaneCoordinates(double cx, double cy, double r) {
    std::vector<long> inds;
    std::function<void(size_t)> reducer(
        [&](size_t i) -> void { inds.push_back(indices_[i]); });
    Reduce(cx, cy, r, &reducer);
    return inds;
  }

  // Returns the number of elements in the buffer.
  size_t size() { return sz_; }

  // Returns the number of floats in the buffer (sz_ * elem_sz_)
  size_t buf_size() { return sz_ * elem_sz_; }

  size_t tree_size() { return 1 << (sz_ / leaf_size_); }

#ifndef TESTONLY
  size_t queried_nodes_count() { return queried_nodes_count_; }

  size_t queried_points_count() { return queried_points_count_; }
#endif

private:
  CKDTree(double *buf, size_t sz, long *indices, double *splits, size_t elem_sz,
          size_t leaf_size, bool pre_initialized)
      : elem_sz_(elem_sz), sz_(sz), leaf_size_(leaf_size) {
    buf_ = buf;
    indices_ = indices;
    splits_ = splits;
    if (pre_initialized) {
      return;
    }
    for (size_t i = 0; i < sz_; i++) {
      indices_[i] = static_cast<long>(i);
    }
    init_tree();
  }

  // Swap elements i, j in buf_;
  // This will swap all field for the i-th and j-th elements, accounting for
  // their columnar ordering.
  void swap(size_t i, size_t j);

  // Copy out all elements of the i-th element into out.
  void get(size_t i, double *out);

  // Set the i-th element with the values in elem, accounting for columnar
  // order.
  void set(size_t i, double *elem, size_t j);

  // Reorder buf_ such that all elements left of the median between [start, end)
  // are less than all elements right of the mediant between [start, end) along
  // the specified dimension.
  double partition(size_t start, size_t end, size_t dimension);

  // Calls reducer with the index of all elements that fall within the circle
  // of radius r at location (cx, cy).
  void Reduce(double cx, double cy, double r,
              std::function<void(size_t)> *reducer);

  // Initialize the CKDTree.
  void init_tree();

  // Pointer to a contiguous buffer of coordinates, in columnar order.
  double *buf_;

  // Lookup array mapping from ordered index to the index of that point
  // in the original buffer before sorting.
  long *indices_;

  // Number of double's per element, laid out in columnar order.
  size_t elem_sz_;

  //  The number of elements in buf_
  size_t sz_;

  // Min number of elements to includes per leaf.
  size_t leaf_size_;

#ifndef TESTONLY
  size_t queried_nodes_count_;
  size_t queried_points_count_;
#endif

  // Array of splits in heap-ordering.
  double *splits_;
};

inline void CKDTree::set(size_t i, double *elem, size_t j) {
  for (size_t d = 0; d < elem_sz_; d++) {
    buf_[d * sz_ + i] = elem[d];
  }
  indices_[i] = static_cast<long>(j);
}

inline void CKDTree::get(size_t i, double *out) {
  for (size_t d = 0; d < elem_sz_; d++) {
    out[d] = buf_[d * sz_ + i];
  }
}

// TODO: Maybe optimize this to skip an extra copy?
inline void CKDTree::swap(size_t i, size_t j) {
  double* i_vals = new double[elem_sz_];
  double* j_vals = new double[elem_sz_];
  int i_idx = indices_[i];
  int j_idx = indices_[j];
  get(i, i_vals);
  get(j, j_vals);
  set(i, j_vals, j_idx);
  set(j, i_vals, i_idx);
  delete[] i_vals;
  delete[] j_vals;
}

inline double CKDTree::partition(size_t start, size_t end, size_t dimension) {
  size_t k = (start + end) / 2;
  size_t l = start;
  size_t ir = end - 1;
  size_t i, j, mid, a_j_idx, a_idx;
  double* a = new double[elem_sz_];
  double* a_j = new double[elem_sz_];

  // Pointer to the first double along the partitioning buffer.
  double *arr = &buf_[sz_ * dimension];
  for (;;) {
    if (ir <= l + 1) {
      if (ir == l + 1 && arr[ir] < arr[l]) {
        swap(l, ir);
      }
      return arr[k];
    }
    mid = (l + ir) >> 1;
    swap(mid, l + 1);
    if (arr[l] > arr[ir]) {
      swap(l, ir);
    }
    if (arr[l + 1] > arr[ir]) {
      swap(l + 1, ir);
    }
    if (arr[l] > arr[l + 1]) {
      swap(l, l + 1);
    }
    i = l + 1;
    j = ir;
    a_idx = indices_[i];
    get(i, a);
    for (;;) {
      do {
        i++;
      } while (arr[i] < a[dimension]);
      do {
        j--;
      } while (arr[j] > a[dimension]);
      if (j < i) {
        break;
      }
      swap(i, j);
    }

    get(j, a_j);
    a_j_idx = indices_[j];
    set(l + 1, a_j, a_j_idx);
    set(j, a, a_idx);
    if (j >= k) {
      ir = j - 1;
    }
    if (j <= k) {
      l = i;
    }
  }
  delete[] a;
  delete[] a_j;
}

inline void CKDTree::init_tree() {
  size_t split = 0;
  if (sz_ == 0 || elem_sz_ == 0) {
    return;
  }
  // queue up tuples of (start_i, end_i, dimension)
  std::queue<std::tuple<size_t, size_t, size_t>> q(
      {std::make_tuple(0, sz_, 0)});
  while (!q.empty()) {
    auto [start, end, dim] = q.front();
    q.pop();

    if (end - start <= leaf_size_) {
      continue;
    }
    size_t midpt = (start + end) / 2;
    splits_[split++] = partition(start, end, dim);
    q.push(std::make_tuple(start, midpt, (dim + 1) % 2));
    q.push(std::make_tuple(midpt, end, (dim + 1) % 2));
  }
}

inline void CKDTree::Reduce(double cx, double cy, double r,
                            std::function<void(size_t)> *reducer) {
#ifndef TESTONLY
  queried_nodes_count_ = 0;
  queried_points_count_ = 0;
#endif
  double r2 = r * r;
  double center[]{cx, cy};
  // queue of tuples of (start_i, end_i, split_index, dimension)
  std::queue<std::tuple<size_t, size_t, size_t, size_t>> q(
      {std::make_tuple(0, sz_, 0, 0)});
  while (!q.empty()) {
    auto [start, end, split, dimension] = q.front();
    q.pop();

    if (end - start <= leaf_size_) {
#ifndef TESTONLY
      queried_nodes_count_++;
#endif
      // We're at a leaf, so apply reducer.
      // TODO: SIMD this. It's tricky because you have to use aligned pointers
      // and start for both x and y may not be aligned.
      //
      // If I want to SIMD this I might need to create a copy of the data
      // so that the x and y buffers are guaranteed aligned.
      for (size_t i = start; i < end; i++) {
#ifndef TESTONLY
        queried_points_count_++;
#endif
        double dx = buf_[i] - cx;
        double dy = buf_[sz_ + i] - cy;
        if (dx * dx + dy * dy < r2) {
          (*reducer)(i);
        }
      }
      continue;
    }
    size_t midpt = (start + end) / 2;
    double split_pt = splits_[split];
    if (center[dimension] - r <= split_pt) {
      // Recurse left
      q.push(std::make_tuple(start, midpt, split * 2 + 1, (dimension + 1) % 2));
    }
    if (center[dimension] + r > split_pt) {
      // Recurse right
      q.push(std::make_tuple(midpt, end, split * 2 + 2, (dimension + 1) % 2));
    }
  }
}

#endif // MIRAGE_CALC_CKD_TREE_H_
