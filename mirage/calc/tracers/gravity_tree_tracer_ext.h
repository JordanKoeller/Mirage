#ifndef MIRAGE_CALC_GRAVITY_TRACER_TREE_H_
#define MIRAGE_CALC_GRAVITY_TRACER_TREE_H_

#include <cstdint>
#define ELEM_SZ 3

#include <array>
#include <cmath>
#include <iostream>
#include <memory>
#include <queue>
#include <vector>

void trace_gravity_tree(double *rays, size_t num_rays, double kap, double gam,
                        double *stars, std::size_t num_stars,
                        double approximation_factor = 0.6);

class GravityTree {
public:
  // Creates a GravityTree inplace.
  // The provided buffer should have stars in columnar order, with
  // coordinates (x, y, m).
  //
  // The GravityTree mutates `buf` inplace, and does not take ownership
  // of the data.
  GravityTree(double *buf, size_t size, double approximation_factor)
      : buf_(buf), sz_(size),
        approximation_factor2_(approximation_factor * approximation_factor) {
    CreateTree();
  }

  // Deflects a singluar ray through the gravity tray.
  // The deflected ray is written to the out parameter
  void Deflect(const double *ray, double *out) const;

private:
  struct Node {
    // indices in buf_ to the data owned by this node.
    // end_ind is exclusive.
    //
    // These MUST best set when creating the Node.
    size_t start_ind;
    size_t end_ind;

    // span of the node.
    // These MUST best set when creating the Node.
    double x_min;
    double x_max;
    double y_min;
    double y_max;

    // Center of mass (x, y, m)
    double com_x;
    double com_y;
    double com_m;

    // a_21, a_22, a_31, a_32, a_41, a_42...
    std::array<double, 10> as;

    // Index of the first child. Note this does not necessarily mean the first
    // child is populated - just where it would be, if it were.
    size_t children;
    uint8_t num_children;
  };

  void CreateTree();

  // Computes Center of mass and moments of a node.
  void ComputeMoments(Node &node);

  // Computes the deflection of a ray from a node using the node
  // multipole expansion.
  //
  // The deflection ray (dx, dy) is written out to *out parameter.
  //
  void DeflectNode(const Node &node, const double *ray, double *out) const;

  // Computes the deflection of a ray by addition contributions from
  // all the individual stars in the node.
  //
  // The deflection ray (dx, dy) is written out to *out parameter.
  //
  void DeflectStars(const Node &node, const double *ray, double *out) const;

  // Swap elements i, j in buf_;
  // This will swap all field for the i-th and j-th elements, accounting for
  // their columnar ordering.
  void Swap(size_t i, size_t j);

  // Partition the data such that all points less than split are left of all
  // points right of split, along the specified axis.
  //
  // Returns the index of the first right value.
  size_t Partition(size_t start_ind, size_t end_ind, double split, size_t axis);

  double *buf_;
  size_t sz_;

  // Apparent width, scaled by distance from the query point, at which to stop
  // approximating lensing from far buckets.
  //
  // This should be a number between 0 and 1.
  double approximation_factor2_;

  size_t leaf_sz_ = 16;
  std::vector<Node> nodes_;
};

inline void GravityTree::ComputeMoments(Node &node) {
  node.com_x = 0.0;
  node.com_y = 0.0;
  node.com_m = 0.0;

  for (size_t i = node.start_ind; i < node.end_ind; i++) {
    node.com_x += buf_[i];
    node.com_y += buf_[sz_ + i];
    node.com_m += buf_[sz_ + sz_ + i];
  }

  node.com_x = node.com_x / static_cast<double>(node.end_ind - node.start_ind);
  node.com_y = node.com_y / static_cast<double>(node.end_ind - node.start_ind);
  node.com_m = node.com_m / static_cast<double>(node.end_ind - node.start_ind);

  for (size_t i = 0; i < node.as.size(); i++) {
    node.as[i] = 0.0;
  }

  for (size_t i = node.start_ind; i < node.end_ind; i++) {
    double m = buf_[sz_ + sz_ + i];

    double dx[7];
    double dy[7];
    dx[0] = buf_[i] - node.com_x;
    dy[0] = buf_[sz_ + i] - node.com_y;
    dx[1] = dx[0];
    dy[1] = dy[0];

    for (int j = 1; j < 6; j++) {
      dx[j + 1] = dx[j] * dx[0];
      dy[j + 1] = dy[j] * dy[0];
    }

    node.as[0] += m * (dx[2] - dy[2]);                                  // a21
    node.as[1] += 2 * m * dx[1] * dy[1];                                //
    node.as[2] += m * (dx[3] - 3 * dx[1] * dy[2]);                      // a31
    node.as[3] += m * (3 * dx[2] * dy[1] - dy[3]);                      // a32
    node.as[4] += m * (dx[4] - 6 * dx[2] * dy[2] + dy[4]);              // a41
    node.as[5] += m * (4 * dx[3] * dy[1] - 4 * dx[1] * dy[3]);          // a42
    node.as[6] += m * (dx[5] - 10 * dx[3] * dy[2] + 5 * dx[1] * dy[4]); // a51
    node.as[7] += m * (5 * dx[4] * dy[1] - 10 * dx[2] * dy[3] + dy[5]); // a52
    node.as[8] +=
        m * (dx[6] - 15 * dx[4] * dy[2] + 15 * dx[2] * dy[4] - dy[6]); // a61
    node.as[9] +=
        m * (6 * dx[5] * dy[1] - 20 * dx[3] * dy[3] + 6 * dx[1] * dy[5]); // a62
  }

  // for (size_t i = node.start_ind; i < node.end_ind; i++) {
  //   double sx = buf_[i];
  //   double sy = buf_[i + sz_];
  //   if (sx > node.x_max || sx < node.x_min) {
  //     std::cout << "#### x OOB " << sx << "\n";
  //   }
  //   if (sy > node.y_max || sy < node.y_min) {
  //     std::cout << "#### y OOB " << sy << "\n";
  //   }
  // }
}

inline void GravityTree::DeflectNode(const Node &node, const double *ray,
                                     double *out) const {
  double dx[8];
  double dy[8];
  double dr[7];

  dx[0] = ray[0] - node.com_x;
  dy[0] = ray[1] - node.com_y;
  dx[1] = dx[0];
  dy[1] = dy[0];

  for (int i = 1; i < 7; i++) {
    dx[i + 1] = dx[i] * dx[0];
    dy[i + 1] = dy[i] * dy[0];
  }

  dr[0] = std::sqrt(dx[2] + dy[2]);
  for (int i = 1; i < 7; i++) {
    dr[i] = std::pow(dr[0], 2 * i + 2);
  }

  // b21, b22, b31, b32, b41 ...
  double bs[10];
  bs[0] = dx[3] - 3 * dx[1] * dy[2];                                  // b21
  bs[1] = 3 * dx[2] * dy[1] - dy[2];                                  // b22
  bs[2] = dx[4] - 6 * dx[2] * dy[2] + dy[4];                          // b31
  bs[3] = 4 * dx[3] * dy[1] - 4 * dx[2] * dy[2];                      // b32
  bs[4] = dx[5] - 10 * dx[3] * dy[2] + 5 * dx[1] * dy[4];             // b41
  bs[5] = 5 * dx[4] * dy[1] - 10 * dx[2] * dy[3] + dy[5];             // b42
  bs[6] = dx[6] - 15 * dx[4] * dy[2] + 15 * dx[2] * dy[4] - dy[6];    // b51
  bs[7] = 6 * dx[5] * dy[1] - 20 * dx[3] * dy[3] + 6 * dx[1] * dy[5]; // b52
  bs[8] = dx[7] - 21 * dx[5] * dy[2] + 35 * dx[3] * dy[4] -
          7 * dx[1] * dy[6]; // b61
  bs[9] = 7 * dx[6] * dy[1] - 35 * dx[4] * dy[3] + 21 * dx[2] * dy[5] -
          dy[7]; // b62

  // Add Monopole
  out[0] = node.com_m * dx[0] / dr[0] / dr[0];
  out[1] = node.com_m * dy[0] / dr[0] / dr[0];

  // Poles 4-pole to 64-pole
  for (int i = 0; i < 5; i++) {
    out[0] +=
        (node.as[i * 2] * bs[i * 2] + node.as[i * 2 + 1] * bs[i * 2 + 1]) /
        dr[i];
    out[1] +=
        (node.as[i * 2 + 1] * bs[i * 2] - node.as[i * 2] * bs[i * 2 + 1]) /
        dr[i];
  }
}

inline void GravityTree::Swap(size_t i, size_t j) {
  double tmp;
  for (size_t e = 0; e < ELEM_SZ; e++) {
    tmp = buf_[e * sz_ + i];
    buf_[e * sz_ + i] = buf_[e * sz_ + j];
    buf_[e * sz_ + j] = tmp;
  }
}

inline void GravityTree::CreateTree() {
  // std::cout << "Creating Tree\n";
  double extrema[4]; // xmin, xmax, ymin, ymax
  extrema[0] = buf_[0];
  extrema[1] = buf_[0];
  extrema[2] = buf_[sz_];
  extrema[3] = buf_[sz_];
  // std::cout << "Computing Extrema\n";
  for (size_t i = 0; i < sz_; i++) {
    if (buf_[i] < extrema[0]) {
      extrema[0] = buf_[i];
    }
    if (buf_[i] > extrema[1]) {
      extrema[1] = buf_[i];
    }
    if (buf_[i + sz_] < extrema[2]) {
      extrema[2] = buf_[i + sz_];
    }
    if (buf_[i + sz_] > extrema[3]) {
      extrema[3] = buf_[i + sz_];
    }
  }

  nodes_.push_back(Node{.start_ind = 0,
                        .end_ind = sz_,
                        .x_min = extrema[0],
                        .x_max = extrema[1],
                        .y_min = extrema[2],
                        .y_max = extrema[3]});
  std::queue<size_t> q({0});

  while (!q.empty()) {
    size_t n = q.front();
    // std::cout << "Queue " << n << "\n";
    const Node node = nodes_[n];

    q.pop();

    if (node.end_ind - node.start_ind <= leaf_sz_ ||
        node.start_ind == node.end_ind) {
      std::cout << "Node [" << node.start_ind << ", " << node.end_ind
                << ") sufficiently split\n";
      continue;
    }

    double vert_split = (node.x_max + node.x_min) / 2.0;
    double horz_split = (node.y_max + node.y_min) / 2.0;
    size_t n_i = nodes_.size();
    // std::cout << "Partitioning node tb  " << n << "\n";
    size_t tb_indsplit = Partition(node.start_ind, node.end_ind, horz_split, 1);
    // std::cout << "Partitioning node tlr " << n << "\n";
    size_t tlr_indsplit = Partition(tb_indsplit, node.end_ind, vert_split, 0);
    // std::cout << "Partitioning node blr " << n << "\n";
    size_t blr_indsplit = Partition(node.start_ind, tb_indsplit, vert_split, 0);
    std::cout << "partitions [" << node.start_ind << ", " << node.end_ind
              << ") tb " << tb_indsplit << " tlr_indsplit " << tlr_indsplit
              << " blr_indsplit " << blr_indsplit << "\n";
    uint8_t num_children = 0;

    // bottom-left
    if (blr_indsplit - node.start_ind > 0) {
      nodes_.push_back(Node{.start_ind = node.start_ind,
                            .end_ind = blr_indsplit,
                            .x_min = node.x_min,
                            .x_max = vert_split,
                            .y_min = node.y_min,
                            .y_max = horz_split});
      q.push(n_i + num_children);
      num_children++;
    }
    // bottom-right
    if (tb_indsplit - blr_indsplit > 0) {
      nodes_.push_back(Node{.start_ind = blr_indsplit,
                            .end_ind = tb_indsplit,
                            .x_min = vert_split,
                            .x_max = node.x_max,
                            .y_min = node.y_min,
                            .y_max = horz_split});
      q.push(n_i + num_children);
      num_children++;
    }
    // top-left
    if (tlr_indsplit - tb_indsplit > 0) {
      nodes_.push_back(Node{.start_ind = tb_indsplit,
                            .end_ind = tlr_indsplit,
                            .x_min = node.x_min,
                            .x_max = vert_split,
                            .y_min = horz_split,
                            .y_max = node.y_max});
      q.push(n_i + num_children);
      num_children++;
    }
    // top-right
    if (node.end_ind - tlr_indsplit > 0) {
      nodes_.push_back(Node{.start_ind = tlr_indsplit,
                            .end_ind = node.end_ind,
                            .x_min = vert_split,
                            .x_max = node.x_max,
                            .y_min = horz_split,
                            .y_max = node.y_max});
      q.push(n_i + num_children);
      num_children++;
    }
    nodes_[n].num_children = num_children;
    nodes_[n].children = n_i;
  }

  // std::cout << "Partitioning done. Computing moments\n";
  for (auto node : nodes_) {
    ComputeMoments(node);
  }
}

inline size_t GravityTree::Partition(size_t start_ind, size_t end_ind,
                                     double split, size_t axis) {
  // use a two pointers algorithm
  size_t p_l = start_ind;
  size_t p_r = end_ind - 1;
  // std::cout << "Partitioning [" << start_ind << ", " << end_ind << "); split
  // "
  // << split << " on axis " << axis << "\n";
  while (p_l <= p_r) {
    if (buf_[axis * sz_ + p_l] <= split) {
      p_l++;
      continue;
    }
    if (buf_[axis * sz_ + p_r] > split) {
      p_r--;
      continue;
    }
    if (buf_[axis * sz_ + p_l] > split) {
      Swap(p_l, p_r);
    }
  }
  // for (size_t i = start_ind; i < end_ind; i++) {
  //   double v = buf_[axis * sz_ + i];
  //   if (i < p_l && v > split) {
  //     std::cout << "### " << v << " TOO BIG at " << i << " > " << split
  //               << " p_l " << p_l << "\n";
  //     break;
  //   }
  //   if (i == p_l && v <= split) {
  //     std::cout << "### p_l included\n";
  //     break;
  //   }
  //   if (i > p_l && v <= split) {
  //     std::cout << "#### " << v << " TOO SMALL at " << i << " < " << split
  //               << " p_l " << p_l << "\n";
  //     break;
  //   }
  // }
  return p_l;
}

inline void GravityTree::Deflect(const double *ray, double *out) const {
  // TODO: Optimize to not require dynamic memory for recursion.
  std::queue<size_t> q({0});
  double deflected[2];
  deflected[0] = 0.0;
  deflected[1] = 0.0;
  size_t node_deflects = 0;
  size_t star_deflects = 0;
  while (!q.empty()) {
    size_t n = q.front();
    q.pop();

    const Node &node = nodes_[n];
    double dx = ray[0] - node.com_x;
    double dy = ray[1] - node.com_y;
    double node_span = node.x_max - node.x_min;
    if (node.end_ind == node.start_ind) {
      continue;
    }

    double erf = 2 * node_span * node_span / (dx * dx + dy * dy);
    std::cout << "Querying[" << n << "] dx=" << dx 
              << ", dy=" << dy << " erf=" << erf << "\n";

    if (erf < approximation_factor2_) {
      node_deflects += (node.end_ind - node.start_ind);
      // std::cout << "Deflecting node" << n << " start_ind=" << node.start_ind
      //           << ", end_ind=" << node.end_ind << "\n";
      DeflectNode(node, ray, deflected);
    } else if (node.num_children > 0) {
      for (size_t i = 0; i < node.num_children; i++) {
        q.push(node.children + i);
      }
    } else {
      // Deflect manually
      star_deflects += (node.end_ind - node.start_ind);
      // std::cout << "Deflecting stars" << n << " start_ind=" << node.start_ind
      //           << ", end_ind=" << node.end_ind << "\n";
      DeflectStars(node, ray, deflected);
    }
  }
  std::cout << "node_deflects=" << node_deflects
            << " star_deflects=" << star_deflects << "\n";
  out[0] = deflected[0];
  out[1] = deflected[1];
}

inline void GravityTree::DeflectStars(const Node &node, const double *ray,
                                      double *out) const {
  for (size_t i = node.start_ind; i < node.end_ind; i++) {
    double dx = ray[0] - buf_[i];
    double dy = ray[1] - buf_[i + sz_];
    double r2 = dx * dx + dy * dy;
    out[0] += buf_[sz_ + sz_ + i] * dx / r2;
    out[1] += buf_[sz_ + sz_ + i] * dy / r2;
  }
}

// Trace the provided rays. The input rays_x and rays_y are out parameters. The
// traced rays are written back to these buffers.
//
void trace_gravity_tree(double *rays, size_t num_rays, double kap, double gam,
                        double *stars, std::size_t num_stars,
                        double approximation_factor) {
  GravityTree tree(stars, num_stars, approximation_factor);
  std::cout << "Gravity Tree Created\n";
  double g_min = 1.0 - gam;
  double g_max = 1.0 + gam;
  for (size_t i = 0; i < num_rays; i++) {
    std::cout << "Tracing ray " << i << "\n";
    double ray[2];
    double out[2];
    ray[0] = rays[i];
    ray[1] = rays[i + num_rays];
    tree.Deflect(ray, out);
    out[0] = g_min * ray[0] - kap * ray[0] - out[0];
    out[1] = g_max * ray[1] - kap * ray[1] - out[1];
    rays[i] = out[0];
    rays[i + num_rays] = out[1];
  }
}

#endif // MIRAGE_CALC_GRAVITY_TRACER_TREE_H_
