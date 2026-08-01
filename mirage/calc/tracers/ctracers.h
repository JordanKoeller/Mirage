/*
 *
 * SIMD Layout
 * ray positions are in a contiguous buffer of x, y values
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
 * Additionally, there are a lot of repetitive values in rays_x and rays_y. since they
 * form a grid that's the cartesian product of x and y strides.
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
 *  1. I can compute ax, ay via simd operations, then do a final reduction of the 
 *     simd elements at the end.
 *     Payoff: 1/vec_size sequential operations
 *     Tradeoff: Have to make a copy of stars_x, stars_y, stars_m to get aligned
 *       buffers (this is fixable). Complexity
 *  2. I can pre-calculate dx, dy on the sparse arrays.
 *     Payoff:  M * N * S subtractions => (M + N) * S subtractions
 *     Tradeoff: M * S + N * S memory
 *
 * 
 */
#include <experimental/simd>
#include <stdfloat>

namespace stdx = std::experimental;

using Float = double;

// using FV = stdx::simd<Float, stdx::simd_abi::fixed_size<16>>;
using FV = stdx::native_simd<Float>;

inline void trace_stars(
    Float ray_x,
    Float ray_y,
    Float* stars_x,
    Float* stars_y,
    Float* stars_m,
    size_t num_stars,
    Float* out_x,
    Float* out_y
) {
    FV* stars_v_x = (FV*) stars_x;
    FV* stars_v_y = (FV*) stars_y;
    FV* stars_v_m = (FV*) stars_m;

    // Accumulate delta from individual stars on a per-element basis.
    FV ray_x_v(ray_x);
    FV ray_y_v(ray_y);
    FV out_x_v(0.0);
    FV out_y_v(0.0);

    // Trace all rays  around stars (vectorized)
    for (size_t s=0; s < num_stars / FV::size(); s++) {
      FV dx = ray_x_v - stars_v_x[s];
      FV dy = ray_y_v - stars_v_y[s];
      FV r = dx * dx + dy * dy;
      out_x_v += stars_v_m[s] * dx / r;
      out_y_v += stars_v_m[s] * dy / r;
    }
    // reduce the out vector.
    for (size_t j=0; j< FV::size(); j++) {
      *out_x -= out_x_v[j];
      *out_y -= out_y_v[j];
    }
    // Catch any leftover stars.
    for (size_t s = (num_stars / FV::size()) * FV::size(); s < num_stars; s++) {
      Float dx = ray_x - stars_x[s];
      Float dy = ray_y - stars_y[s];
      Float r = dx * dx + dy * dy;
      *out_x -= stars_m[s] * dx / r;
      *out_y -= stars_m[s] * dy / r;
    }
}

// Trace the provided rays. The input rays_x and rays_y are out parameters. The traced rays
// are written back to these buffers.
void trace(Float* rays_x, Float* rays_y, size_t num_rays, Float kap, Float gam,
          Float* stars_m, Float* stars_x, Float* stars_y, size_t num_stars) {
  Float g_min = 1.0 - gam;
  Float g_max = 1.0 + gam;

  Float* stars_v_x = static_cast<Float*>(
    std::aligned_alloc(stdx::memory_alignment_v<FV>,
    (num_stars / FV::size() + 1) * stdx::memory_alignment_v<FV>)
  );
  Float* stars_v_y = static_cast<Float*>(
    std::aligned_alloc(stdx::memory_alignment_v<FV>,
    (num_stars / FV::size() + 1) * stdx::memory_alignment_v<FV>)
  );
  Float* stars_v_m = static_cast<Float*>(
    std::aligned_alloc(stdx::memory_alignment_v<FV>,
    (num_stars / FV::size() + 1) * stdx::memory_alignment_v<FV>)
  );
  std::memcpy(
    static_cast<void*>(stars_v_x),
    static_cast<void*>(stars_x),
    sizeof(Float) * num_stars);
  std::memcpy(
    static_cast<void*>(stars_v_y),
    static_cast<void*>(stars_y),
    sizeof(Float) * num_stars);
  std::memcpy(
    static_cast<void*>(stars_v_m),
    static_cast<void*>(stars_m),
    sizeof(Float) * num_stars);

  for (size_t i=0; i < num_rays; i++) {
    Float ray_x = rays_x[i];
    Float ray_y = rays_y[i];

    // Macrolensing effects
    rays_x[i] = g_min * ray_x - kap * ray_x;
    rays_y[i] = g_max * ray_y - kap * ray_y;


    trace_stars(
      ray_x,
      ray_y,
      stars_v_x,
      stars_v_y,
      stars_v_m,
      num_stars,
      &rays_x[i],
      &rays_y[i]);
  }
}


