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
    double as[7][3];

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

  size_t leaf_sz_ = 4;
  std::vector<Node> nodes_;
};

inline void GravityTree::ComputeMoments(Node &node) {
  for (size_t i = node.start_ind; i < node.end_ind; i++) {
    double sx = buf_[i];
    double sy = buf_[i + sz_];
    if (sx > node.x_max || sx < node.x_min) {
      std::cout << "#### x OOB " << sx << "not in [" << node.x_min << " "
                << node.x_max << "] \n";
    }
    if (sy > node.y_max || sy < node.y_min) {
      std::cout << "#### y OOB " << sy << "not in [" << node.y_min << " "
                << node.y_max << "] \n";
    }
  }
  node.com_x = 0.0;
  node.com_y = 0.0;
  node.com_m = 0.0;

  // center of mass is weighted average of positions.
  for (size_t i = node.start_ind; i < node.end_ind; i++) {
    double m = buf_[sz_ + sz_ + i];
    node.com_x += buf_[i] * m;
    node.com_y += buf_[sz_ + i] * m;
    node.com_m += m;
  }

  node.com_x = node.com_x / node.com_m;
  node.com_y = node.com_y / node.com_m;

  // std::cout << "Center =" << node.com_x << " " << node.com_y
  //           << "; Midpt =" << (node.x_max + node.x_min) / 2.0 << " "
  //           << (node.y_max + node.y_min) / 2.0 << " RangeX = [" << node.x_min
  //           << " " << node.x_max << "] RangeY = [" << node.y_min << " "
  //           << node.y_max << "]\n";

  for (size_t i = 0; i < 7; i++) {
    node.as[i][0] = 0.0;
    node.as[i][1] = 0.0;
    node.as[i][2] = 0.0;
  }

  for (size_t i = node.start_ind; i < node.end_ind; i++) {
    double m = buf_[sz_ + sz_ + i];

    double d1[7];
    double d2[7];
    d1[0] = buf_[i] - node.com_x;
    d2[0] = buf_[sz_ + i] - node.com_y;
    d1[1] = d1[0];
    d2[1] = d2[0];
    for (int j = 1; j < 6; j++) {
      d1[j + 1] = d1[j] * d1[1];
      d2[j + 1] = d2[j] * d2[1];
    }

    node.as[2][1] += m * (d1[2] - d2[2]);
    node.as[2][2] += 2.0 * m * d1[1] * d2[1];
    node.as[3][1] += m * (d1[3] - 3.0 * d1[1] * d2[2]);
    node.as[3][2] += m * (3.0 * d1[2] * d2[1] - d2[3]);
    node.as[4][1] += m * (d1[4] - 6.0 * d1[2] * d2[2] + d2[4]);
    node.as[4][2] += m * (4.0 * d1[3] * d2[1] - 4.0 * d1[1] * d2[3]);
    node.as[5][1] += m * (d1[5] - 10.0 * d1[3] * d2[2] + 5.0 * d1[1] * d2[4]);
    node.as[5][2] += m * (5.0 * d1[4] * d2[1] - 10.0 * d1[2] * d2[3] + d2[5]);
    node.as[6][1] +=
        m * (d1[6] - 15.0 * d1[4] * d2[2] + 15.0 * d1[2] * d2[4] - d2[6]);
    node.as[6][2] +=
        m * (6.0 * d1[5] * d2[1] - 20.0 * d1[3] * d2[3] + 6.0 * d1[1] * d2[5]);

  }
  for (size_t i = 2; i < 7; i++) {
    std::cout << "a" << i << "1=" << node.as[i][1] << " a" << i << "2=" << node.as[i][2] << " ";
  }
  std::cout << std::endl;
}

inline void GravityTree::DeflectNode(const Node &node, const double *ray,
                                     double *out) const {
  double x1[8];
  double x2[8];
  x1[0] = ray[0] - node.com_x;
  x2[0] = ray[1] - node.com_y;
  x1[1] = x1[0];
  x2[1] = x2[0];
  for (int i = 1; i < 7; i++) {
    x1[i + 1] = x1[i] * x1[1];
    x2[i + 1] = x2[i] * x2[1];
  }

  // b21, b22, b31, b32, b41 ...
  double bs[7][3];
  for (int i = 0; i < 7; i++) {
    bs[i][0] = 0.0;
    bs[i][1] = 0.0;
    bs[i][2] = 0.0;
  }
  bs[2][1] = x1[3] - 3.0 * x1[1] * x2[2];
  bs[2][2] = 3.0 * x1[2] * x2[1] - x2[2];
  bs[3][1] = x1[4] - 6.0 * x1[2] * x2[2] + x2[4];
  bs[3][2] = 4.0 * x1[3] * x2[1] - 4 * x1[2] * x2[2];
  bs[4][1] = x1[5] - 10.0 * x1[3] * x2[2] + 5.0 * x1[1] * x2[4];
  bs[4][2] = 5.0 * x1[4] * x2[1] - 10.0 * x1[2] * x2[3] + x2[5];
  bs[5][1] = x1[6] - 15.0 * x1[4] * x2[2] + 15.0 * x1[2] * x2[4] - x2[6];
  bs[5][2] = 6.0 * x1[5] * x2[1] - 20.0 * x1[3] * x2[3] + 6.0 * x1[1] * x2[5];
  bs[6][1] =
      x1[7] - 21.0 * x1[5] * x2[2] + 35.0 * x1[3] * x2[4] - 7.0 * x1[1] * x2[6];
  bs[6][2] =
      7.0 * x1[6] * x2[1] - 35.0 * x1[4] * x2[3] + 21.0 * x1[2] * x2[5] - x2[7];

  for (size_t i = 0; i < 7; i++) {
    std::cout << "b" << i << "1=" << bs[i][1] << " b" << i << "2=" << bs[i][2] << " ";
  }
  std::cout << std::endl;

  double r[15];
  r[0] = sqrt(x1[1] * x1[1] + x2[1] * x2[1]);
  r[1] = r[0];
  for (size_t i = 1; i < 14; i++) {
    r[i + 1] = r[i] * r[1];
  }

  // Add Monopole
  out[0] = node.com_m * x1[1] / r[2];
  out[1] = node.com_m * x2[1] / r[2];

  // Note: Dipole is excluded because the dipole is always zero.

  // Poles 4-pole to 64-pole
  for (int k = 1; k < 7; k++) {
    out[0] += 1.0 / r[2 * k + 2] *
              (node.as[k][1] * bs[k][1] + node.as[k][2] * bs[k][2]);
    out[1] += 1.0 / r[2 * k + 2] *
              (node.as[k][2] * bs[k][1] - node.as[k][1] * bs[k][2]);
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

  double span = extrema[1] - extrema[0];
  double cx = (extrema[1] + extrema[0]) / 2.0;
  double cy = (extrema[3] + extrema[2]) / 2.0;
  if (extrema[3] - extrema[2] > span) {
    span = extrema[3] - extrema[2];
  }
  span /= 2.0;

  nodes_.push_back(Node{.start_ind = 0,
                        .end_ind = sz_,
                        .x_min = cx - span,
                        .x_max = cx + span,
                        .y_min = cy - span,
                        .y_max = cy + span});
  std::queue<size_t> q({0});

  while (!q.empty()) {
    size_t n = q.front();
    // std::cout << "Queue " << n << "\n";
    const Node node = nodes_[n];

    q.pop();
    // std::cout << "Dims x=" << node.x_min << ", " << node.x_max
    //           << "; y=" << node.y_min << ", " << node.y_max << "\n";

    if (node.end_ind - node.start_ind <= leaf_sz_ ||
        node.start_ind == node.end_ind) {
      // std::cout << "Node [" << node.start_ind << ", " << node.end_ind
      //           << ") sufficiently split\n";
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
    // std::cout << "Partitioning [" << node.start_ind << ", " << node.end_ind
    //           << ") tb " << tb_indsplit << " tlr_indsplit " << tlr_indsplit
    //           << " blr_indsplit " << blr_indsplit << "\n";
    // std::cout << "Dims x=" << node.x_min << ", " << vert_split << ", "
    //           << node.x_max << "; y=" << node.y_min << ", " << horz_split
    //           << ", " << node.y_max << "\n";
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

  for (auto &node : nodes_) {
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
  for (size_t i = start_ind; i < end_ind; i++) {
    double v = buf_[axis * sz_ + i];
    if (i < p_l && v > split) {
      std::cout << "### " << v << " TOO BIG at " << i << " > " << split
                << " p_l " << p_l << "\n";
      break;
    }
    if (i == p_l && v <= split) {
      std::cout << "### p_l included\n";
      break;
    }
    if (i > p_l && v <= split) {
      std::cout << "#### " << v << " TOO SMALL at " << i << " < " << split
                << " p_l " << p_l << "\n";
      break;
    }
  }
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
