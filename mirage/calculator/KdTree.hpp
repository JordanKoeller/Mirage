#include <vector>
#include <queue>
#include <iostream>

typedef int Uint;
typedef double Float;

using std::vector;
using std::queue;

struct KdTreeNode {
  Uint startIndex;
  Uint endIndex;
  Float split;
  Uint dimension;
};

class KdTree {
private:
  vector<Float> data;
  vector<Uint> indices;
  vector<KdTreeNode> partitions;
  Uint stride;
  Uint nodeSize;

public:

  KdTree(Float* buffer, Uint s, Uint numPoints) {
    stride = s;
    nodeSize = 8;
    data.reserve(numPoints * stride);
    indices.reserve(numPoints);
    for (Uint i=0; i < numPoints; i++) {
      indices.push_back(i);
      for (Uint j=0; j < stride; j++) {
        data.push_back(buffer[i*stride+j]);
      }
    }
    queue<KdTreeNode> splits_queue;
    splits_queue.emplace(0, numPoints, 0.0, 0);
    while (splits_queue.size() > 0) {
      KdTreeNode& node = splits_queue.front();
      if (node.endIndex - node.startIndex > nodeSize) {
        partition(node);
        Uint dim = (node.dimension + 1) % stride;
        Uint midIndex = (node.startIndex + node.endIndex) / 2;
        splits_queue.emplace(node.startIndex, midIndex, 0.0, dim);
        splits_queue.emplace(midIndex, node.endIndex, 0.0, dim);
      }
      partitions.emplace_back(node.startIndex, node.endIndex, node.split, node.dimension);
      splits_queue.pop();
    }
  }

private:
  void partition(KdTreeNode& node) {

  }

};