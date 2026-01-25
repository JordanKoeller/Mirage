#ifndef MIRAGE_CALC_CKD_TREE_H_
#define MIRAGE_CALC_CKD_TREE_H_

#include <vector>
#include <queue>
#include <functional>
#include <stdfloat>
#include <iostream>

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
   //   buf: Pointer to the front of the buffer containing coordinates in columnar order.
   //   sz: Number of elements in buf.
   //   has_magnification: If true, each element of buf includes a magnification coefficient.
   //   leaf_size: The number of elements to include in each leaf node.
   CKDTree(double* buf, size_t sz, bool has_magnification, size_t leaf_size)
     : buf_(buf), elem_sz_(has_magnification ? 3 : 2), sz_(sz), leaf_size_(leaf_size) {
       init_tree();
     }

   // Return the number of elements in the tree that are within the circle of
   // radius r at location (cx, cy).
   size_t PointsInCircle(double cx, double cy, double r) {
     size_t count = 0;
     std::function<void(size_t)> reducer([&](size_t i)  -> void {
       count++;
     });
     Reduce(cx, cy, r, &reducer);
     return count;
   }

   // Return the magnification coefficient for the specified circle of radius
   // r at location (cx, cy).
   //
   // If the tree does not contain magnification data 0 is returned.
   double MagnificationCoefficient(double cx, double cy, double r) {
     if (elem_sz_ == 2) {
       return 0.0;
     }
     double mag = 0.0;
     std::function<void(size_t)> reducer([&](size_t i) -> void {
       mag += buf_[sz_ * 2 + i];
     });
     Reduce(cx, cy, r, &reducer);
     return mag;
   }
 private:

   // Swap elements i, j in buf_;
   // This will swap all field for the i-th and j-th elements, accounting for
   // their columnar ordering.
   void swap(size_t i, size_t j);

   // Copy out all elements of the i-th element into out.
   void get(size_t i, double* out);

   // Set the i-th element with the values in elem, accounting for columnar order.
   void set(size_t i, double* elem);

   // Reorder buf_ such that all elements left of the median between [start, end)
   // are less than all elements right of the mediant between [start, end) along
   // the specified dimension.
   double partition(size_t start, size_t end, size_t dimension);

   // Calls reducer with the index of all elements that fall within the circle
   // of radius r at location (cx, cy).
   void Reduce(double cx, double cy, double r, std::function<void(size_t)>* reducer);

   // Initialize the CKDTree.
   void init_tree();

   // Pointer to a contiguous buffer of coordinates, in columnar order.
   double* buf_;
  
   // Number of double's per element, laid out in columnar order.
   size_t elem_sz_;

   //  The number of elements in buf_
   size_t sz_;

   // Min number of elements to includes per leaf.
   size_t leaf_size_;

   // Array of splits in heap-ordering.
   std::vector<double> splits_;

};

inline void CKDTree::set(size_t i, double* elem) {
  for (size_t d=0; d < elem_sz_; d++) {
    buf_[d * sz_ + i] = elem[d];
  }
}

inline void CKDTree::get(size_t i, double* out) {
  for (size_t d=0; d < elem_sz_; d++) {
    out[d] = buf_[d * sz_ + i];
  }
}

// TODO: Maybe optimize this to skip an extra copy?
inline void CKDTree::swap(size_t i, size_t j) {
  double i_vals[elem_sz_];
  double j_vals[elem_sz_];
  get(i, i_vals);
  get(j, j_vals);
  set(i, j_vals);
  set(j, i_vals);
}


inline double CKDTree::partition(size_t start, size_t end, size_t dimension) {
  size_t k = (start + end) / 2;
  size_t l = start;
  size_t ir = end - 1;
  size_t i, j, mid;
  double a[elem_sz_];
  double a_j[elem_sz_];

  // Pointer to the first double along the partitioning buffer.
  double* arr = &buf_[sz_*dimension]; 
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
    if (arr[l+1] > arr[ir]) {
      swap(l+1, ir);
    }
    if (arr[l] > arr[l+1]) {
      swap(l, l+1);
    }
    i = l + 1;
    j = ir;
    get(l + 1, a);
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
    set(l + 1, a_j);
    set(j, a);
    if (j >= k) {
      ir = j - 1;
    }
    if (j <= k) {
      l = i;
    }
  }
}

inline void CKDTree::init_tree() {
  // queue up tuples of (start_i, end_i, dimension)
  std::queue<std::tuple<size_t, size_t, size_t>> q({std::make_tuple(0, sz_, 0)});
  while (!q.empty()) {
    auto [start, end, dim] = q.front();
    q.pop();

    size_t midpt = (start + end) / 2;
    splits_.push_back(partition(start, end, dim));
    if ((end-start) / 2 <= leaf_size_) {
      continue;
    }
    q.push(std::make_tuple(start, midpt, (dim + 1) % 2));
    q.push(std::make_tuple(midpt, end, (dim + 1) % 2));
  }
}

inline void CKDTree::Reduce(double cx, double cy, double r, std::function<void(size_t)>* reducer) {
  double r2 = r * r;
  double center[]{cx, cy};
  // queue of tuples of (start_i, end_i, split_index, dimension)
  std::queue<std::tuple<size_t, size_t, size_t, size_t>> q({std::make_tuple(0, sz_, 0, 0)});
  while (!q.empty()) {
    auto [start, end, split, dimension]= q.front();
    q.pop();

    if (split * 2 >= splits_.size()) {
      // We're at a leaf, so apply reducer.
      // TODO: SIMD this. It's tricky because you have to use aligned pointers
      // and start for both x and y may not be aligned.
      // 
      // If I want to SIMD this I might need to create a copy of the data
      // so that the x and y buffers are guaranteed aligned.
      for (size_t i = start; i < end; i++) {
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
      q.push(std::make_tuple(start, midpt, split*2 + 1, (dimension + 1) % 2));
    }
    if (center[dimension] + r > split_pt) {
      // Recurse rigth
      q.push(std::make_tuple(midpt, end, split*2 + 2, (dimension + 1) % 2));
    }
  }
}


#endif // MIRAGE_CALC_CKD_TREE_H_
