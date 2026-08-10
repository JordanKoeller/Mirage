/*
 *
 * SIMD Layout
 * ray positions are in a contiguous buffer of x, y values
 *
 *
 * rays_x = [x1, x2, x3, ...]
 * rays_y = [y1, y2, y3, ...]
 *
 * stars_x = [sx1, sx2, sx3, ...]
 * stars_y = [sy1, sy2, sy3, ...]
 * stars_m = [sm1, sm2, sm3, ...]
 *
 *
 * Note that it is safe to assume that there are far fewer stars than rays.
 *
 * Additionally, there are a lot of repetitive values in rays_x and rays_y.
 * since they form a grid that's the cartesian product of x and y strides.
 *
 * The basic algorithm is
 *
 * for (x, y) in zip(rays_x, rays_y):
 *   ax = x_0 # From kap / gam
 *   ay = y_0 # From kap / gam
 *   for (sx, sy, sm) in zip(stars_x, stars_y, stars_m):
 *     dx = sx - x
 *     dy = sy - y
 *     r2 = dx * dx + dy * dy
 *     ax += sm * dx / r2
 *     ay += sm * dy / r2
 *  x = ax
 *  y = ax
 *
 *  Optimizations:
 *
 *  1. I can compute ax, ay via simd operations, then do a final reduction of
 * the simd elements at the end. Payoff: 1/vec_size sequential operations
 *     Tradeoff: Have to make a copy of stars_x, stars_y, stars_m to get aligned
 *       buffers (this is fixable). Complexity
 *  2. I can pre-calculate dx, dy on the sparse arrays.
 *     Payoff:  M * N * S subtractions => (M + N) * S subtractions
 *     Tradeoff: M * S + N * S memory
 *
 *
 */

#include <iostream>
#include <stdfloat>

#define XSTR(x) STR(x)
#define STR(x) #x

#ifdef __has_include
#if __has_include(<experimental/simd>)
#define using_simd

#include <experimental/simd>
namespace stdx = std::experimental;
#endif
#endif

#ifdef using_simd
#define has_simd true
#else
#define has_simd false
#endif

#pragma message "Compiling with simd: " XSTR(has_simd)

using Float = double;

inline void trace_no_simd(Float *rays_x, Float *rays_y, std::size_t num_rays,
                          Float kap, Float gam, Float *stars_x, Float *stars_y,
                          Float *stars_m, std::size_t num_stars,
                          bool include_macro) {
  Float g_min = 1.0 - gam;
  Float g_max = 1.0 + gam;
  Float rx, ry;
  for (std::size_t i = 0; i < num_rays; i++) {
    rx = rays_x[i];
    ry = rays_y[i];

    if (include_macro) {
      rays_x[i] = g_min * rx - kap * rx;
      rays_y[i] = g_max * ry - kap * ry;
    }

    for (std::size_t s = 0; s < num_stars; s++) {
      Float dx = rx - stars_x[s];
      Float dy = ry - stars_y[s];
      Float r = dx * dx + dy * dy;
      rays_x[i] -= stars_m[s] * dx / r;
      rays_y[i] -= stars_m[s] * dy / r;
    }
  }
}

#ifdef using_simd
using FV = stdx::native_simd<Float>;

Float *aligned_copy(Float *buffer, std::size_t len) {
  Float *aligned_buf = static_cast<Float *>(std::aligned_alloc(
      stdx::memory_alignment_v<FV>,
      (len / FV::size() + 1) * stdx::memory_alignment_v<FV>));
  std::memcpy(static_cast<void *>(aligned_buf), static_cast<void *>(buffer),
              sizeof(Float) * len);

  return aligned_buf;
}

/*
 * Trace rays using SIMD instruction set.
 *
 * None of the Float* pointers are assumed axis-aligned, nor
 * is it assumed that the number of stars or rays is divisible
 * by the simd element size.
 *
 *
 * The traced ray results are written out to out_x, out_y
 */
inline void trace_simd(Float *rays_x, Float *rays_y, std::size_t num_rays,
                       Float kap, Float gam, Float *stars_x, Float *stars_y,
                       Float *stars_m, std::size_t num_stars) {
  FV *stars_x_buf = (FV *)(aligned_copy(stars_x, num_stars));
  FV *stars_y_buf = (FV *)(aligned_copy(stars_y, num_stars));
  FV *stars_m_buf = (FV *)(aligned_copy(stars_m, num_stars));

  Float g_min = 1.0 - gam;
  Float g_max = 1.0 + gam;

  // Trace all rays  around stars (vectorized)
  for (std::size_t r = 0; r < num_rays; r++) {
    Float rx = rays_x[r];
    Float ry = rays_y[r];
    FV ray_x(rx);
    FV ray_y(ry);
    FV out_x_v(0.0);
    FV out_y_v(0.0);

    rays_x[r] = g_min * rx - kap * rx;
    rays_y[r] = g_max * ry - kap * ry;

    for (std::size_t s = 0; s < num_stars / FV::size(); s++) {
      FV dx = ray_x - stars_x_buf[s];
      FV dy = ray_y - stars_y_buf[s];
      FV r = dx * dx + dy * dy;
      out_x_v += stars_m_buf[s] * dx / r;
      out_y_v += stars_m_buf[s] * dy / r;
    }
    // reduce the out vector.
    for (std::size_t j = 0; j < FV::size(); j++) {
      rays_x[r] -= out_x_v[j];
      rays_y[r] -= out_y_v[j];
    }
  }

  // Trace any leftover stars.
  size_t last_star_ind = (num_stars / FV::size()) * FV::size();
  trace_no_simd(rays_x, rays_y, num_rays, kap, gam, &stars_x[last_star_ind],
                &stars_y[last_star_ind], &stars_m[last_star_ind],
                num_stars - last_star_ind, false);

  delete[] stars_x_buf;
  delete[] stars_y_buf;
  delete[] stars_m_buf;
}
#endif

// Trace the provided rays. The input rays_x and rays_y are out parameters. The
// traced rays are written back to these buffers.
//
void trace(Float *rays_x, Float *rays_y, std::size_t num_rays, Float kap,
           Float gam, Float *stars_m, Float *stars_x, Float *stars_y,
           std::size_t num_stars, int allow_simd) {

#ifdef using_simd
  if (allow_simd) {
    trace_simd(rays_x, rays_y, num_rays, kap, gam, stars_x, stars_y, stars_m,
               num_stars);
    return;
  }
#endif
  trace_no_simd(rays_x, rays_y, num_rays, kap, gam, stars_x, stars_y, stars_m,
                num_stars, true);
}

bool supports_simd() {
#ifdef using_simd
  return true;
#endif
  return false;
}
