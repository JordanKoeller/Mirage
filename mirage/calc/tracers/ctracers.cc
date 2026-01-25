void add_vecs_from_floats(Float* a, Float* b, int64_t sz) {
  FV* o_v = (FV*) a;
  FV* a_v = (FV*) a;
  FV* b_v = (FV*) b;



  // Do all the math (vectorized).
  for (size_t i=0; i < sz / FV::size(); i++) {
    o_v[i] = a_v[i] + b_v[i];
  }
  // Repeat it again using non-vector representations in case not all points
  // could be vectorized.
  for (size_t i=(sz / FV::size()) * FV::size(); i < sz; i++) {
    a[i] = a[i] + b[i];
  }

}

void print(const std::vector<Float> &v) {
  std::cout << "[";
  for (auto vv : v) {
    std::cout << vv << ", ";
  }
  std::cout << "]\n";
}

int main(void) {
  std::vector<Float>a, b;
  for (int i=0; i < 255; i++) {
    a.push_back((Float) i);
    b.push_back((Float) i);
  }

  std::cout << "vec sz = " << FV::size() << "\n";

  std::cout << "a = ";
  print(a);
  std::cout << "b = ";
  print(b);

  add_vecs_from_floats(a.data(), b.data(), a.size());
  std::cout << "o = ";
  print(a);
}
