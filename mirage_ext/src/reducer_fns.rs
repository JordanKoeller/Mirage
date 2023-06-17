// use ndarray;

pub mod reducer_fns_mod {

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

}
