

template<typename T>
__global__ void (
    const T* rays_x,
    const T* rays_y,
    T kap,
    T gam,
    const T* stars_x,
    const T* stars_y,
    const T* stars_m,
    size_t num_stars,
    T* out_x,
    T* out_y,
) {
    const unsigned int tid = threadIdx.x + blockIdx.x * blockDim.x;
    T g_min = 1.0 - gam;
    T g_max = 1.0 + gam;
    T rx = rays_x[tid];
    T ry = rays_y[tid];

    out_x[tid] = g_min * rx - kap * rx;
    out_y[tid] = g_max * ry - kap * ry;

    for (siz_t s=0; s < num_stars; s++) {
        T dx = rx - stars_x[s];
        T dy = ry - stars_y[s];
        T r2 = dx * dx + dy * dy;
        out_x[tid] -= stars_m[s] * dx / r2;
        out_y[tid] -= stars_m[s] * dx / r2;
    }
}