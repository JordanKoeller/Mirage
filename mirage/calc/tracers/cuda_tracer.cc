

template<typename T>
__global__ void ray_trace_cuda(
    const T* rays_x,
    const T* rays_y,
    size_t num_rays,
    T kap,
    T gam,
    const T* stars_x,
    const T* stars_y,
    const T* stars_m,
    size_t num_stars,
    T* out_x,
    T* out_y
) {
    const unsigned int tid = threadIdx.x + blockIdx.x * blockDim.x;
    T g_min = 1.0 - gam;
    T g_max = 1.0 + gam;
    for (size_t i=tid; i < num_rays; i += gridDim.x * blockDim.x) {
        T rx = rays_x[i];
        T ry = rays_y[i];
    
        out_x[i] = g_min * rx - kap * rx;
        out_y[i] = g_max * ry - kap * ry;
    
        for (size_t s=0; s < num_stars; s++) {
            T dx = rx - stars_x[s];
            T dy = ry - stars_y[s];
            T r2 = dx * dx + dy * dy;
            out_x[i] -= stars_m[s] * dx / r2;
            out_y[i] -= stars_m[s] * dy / r2;
        }
    }
}