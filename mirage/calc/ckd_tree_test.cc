#include <iostream>
#include <random>
#include <stdfloat>
#include <algorithm>

#include "ckd_tree.h"

using ::std::cout;
using ::std::float64_t;

template<typename Numeric, typename Generator = std::mt19937>
Numeric random(Numeric from, Numeric to)
{
    thread_local static Generator gen(std::random_device{}());

    using dist_type = typename std::conditional
    <
        std::is_integral<Numeric>::value
        , std::uniform_int_distribution<Numeric>
        , std::uniform_real_distribution<Numeric>
    >::type;

    thread_local static dist_type dist;

    return dist(gen, typename dist_type::param_type{from, to});
}

std::vector<float64_t> CreatePoints(size_t num_points, size_t num_dims) {
  std::vector<float64_t> arr;
  for (size_t i=0; i < num_points * num_dims; i++) {
    arr.push_back(random<float64_t>(-10.0, 10.0));
  }
  return arr;
}

size_t BruteForceCount(
    const std::vector<float64_t> arr, size_t sz,
    float64_t cx, float64_t cy, float64_t r
) {
  size_t count = 0;
  float64_t r2 = r * r;
  for (int i=0; i < sz; i++) {
    float64_t dx = arr[i] - cx;
    float64_t dy = arr[i + sz] - cy;
    if (dx * dx + dy * dy < r2) {
      count++;
    }
  }
  return count;
}

float64_t BruteForceMag(
    const std::vector<float64_t> arr, size_t sz,
    float64_t cx, float64_t cy, float64_t r
) {
  float64_t mag;
  float64_t r2 = r * r;
  for (int i=0; i < sz; i++) {
    float64_t dx = arr[i] - cx;
    float64_t dy = arr[i + sz] - cy;
    if (dx * dx + dy * dy < r2) {
      mag += arr[i + sz * 2];
    }
  }
  return mag;
}

void Print(const std::vector<float64_t>& arr, size_t sz) {
  cout << "[";
  for (int i=0; i < sz; i++) {
    cout << "(" << arr[i] << ", " << arr[i + sz] << "), ";
  }
  cout << "]\n";
}

void TestWithoutMags() {
  std::vector<size_t> sizes{
    100, 500, 1000, 1001, 5003, 1024, 2049, 7919, 5297, 5298, 7723, 10000, 10023, 10240,
      50023, 50763,
      100023, 100452, 100421,
      500000,
      1000000,
      5429457,
      500237,
      765324,
  };
  std::sort(sizes.begin(), sizes.end());

  for (auto sz : sizes) {
    auto arr = CreatePoints(sz, 2);
    auto arrCopy = arr;
    CKDTree tree(arr.data(), sz, false, 128);
    size_t tree_val = tree.PointsInCircle(-2.0, 3.4, 2.4);
    size_t bf_val =  BruteForceCount(arrCopy, sz, -2.0, 3.4, 2.4);
    if (tree_val != bf_val) {
      cout << "[" << sz << "]: " << tree_val << " != " << bf_val << "\n";
    } else {
      cout << "[" << sz << "]: PASS (" << tree_val << ")\n";
    }
  }
}

void TestWithMags() {
  std::vector<size_t> sizes{
    100, 500, 1000, 1001, 5003, 1024, 2049, 7919, 5297, 5298, 7723, 10000, 10023, 10240,
      50023, 50763,
      100023, 100452, 100421,
      500000,
      1000000,
      5429457,
      500237,
      765324,
  };
  std::sort(sizes.begin(), sizes.end());

  // std::vector<size_t> sizes{500};

  for (auto sz : sizes) {
    auto arr = CreatePoints(sz, 3);
    auto arrCopy = arr;
    CKDTree tree(arr.data(), sz, true, 64);
    float64_t tree_val = tree.MagnificationCoefficient(-2.0, 3.4, 2.4);
    float64_t bf_val =  BruteForceMag(arrCopy, sz, -2.0, 3.4, 2.4);
    // Allow for floating point differences.
      if ((tree_val - bf_val) / (tree_val + bf_val) / 2 > 1e-7) {
      cout << "[" << sz << "]: " << tree_val << " != " << bf_val << "\n";
    } else {
      cout << "[" << sz << "]: PASS (" << tree_val << ")\n";
    }
  }

}

int main(void) {
  TestWithoutMags();
  TestWithMags();
}
