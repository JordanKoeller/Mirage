// use ndarray;

pub mod reducer_fns_mod {
  use crate::kiddo_tree::KiddoTree;

  // Converts a list of tuples of [x, y] indices to a rendered image
  pub fn reduce_lensed_image(
    indices: ndarray::ArrayView2<usize>,
    dims: ndarray::ArrayView1<usize>,
    hit_color: ndarray::ArrayView1<u8>,
  ) -> ndarray::Array3<u8> {
    let mut data: ndarray::Array3<u8> = ndarray::Array3::zeros((dims[0], dims[1], 3usize));
    for i in 0..indices.shape()[0] {
      data[[indices[[i, 0]], indices[[i, 1]], 0]] = hit_color[0];
      data[[indices[[i, 0]], indices[[i, 1]], 1]] = hit_color[1];
      data[[indices[[i, 0]], indices[[i, 1]], 2]] = hit_color[2];
    }

    data
  }

  pub fn reduce_magmap(
    tree: &KiddoTree,
    query_points: ndarray::ArrayView3<f64>,
    radius: f64,
  ) -> ndarray::Array2<usize> {
    let query_shape = [query_points.shape()[0], query_points.shape()[1]];
    ndarray::Array2::from_shape_fn(query_shape, |(i, j)| {
      tree.query_count_rs(
        *query_points.get((i, j, 0)).unwrap(),
        *query_points.get((i, j, 1)).unwrap(),
        radius,
      )
    })
  }
}
