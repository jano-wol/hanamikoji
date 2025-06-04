#include <algorithm>
#include <fstream>
#include <iostream>
#include <map>
#include <numeric>
#include <sstream>
#include <string>
#include <vector>

// Generate all 12 permutations of the vector based on 3! × 2! symmetries
std::vector<std::vector<int32_t>> generate_orbit(const std::vector<int32_t>& v)
{
  std::vector<std::vector<int32_t>> orbit;
  std::vector<int> perm3 = {0, 1, 2};
  std::vector<int> perm2 = {3, 4};

  do {
    do {
      std::vector<int32_t> w = v;
      w[0] = v[perm3[0]];
      w[1] = v[perm3[1]];
      w[2] = v[perm3[2]];
      w[3] = v[perm2[0]];
      w[4] = v[perm2[1]];
      orbit.push_back(w);
    } while (std::next_permutation(perm2.begin(), perm2.end()));
  } while (std::next_permutation(perm3.begin(), perm3.end()));

  return orbit;
}

// Read input file into std::map
std::map<std::vector<int32_t>, double> read_input(const std::string& filename)
{
  std::ifstream in(filename);
  if (!in) {
    std::cerr << "Error: Cannot open file " << filename << "\n";
    std::exit(1);
  }

  std::map<std::vector<int32_t>, double> data;
  std::string line;

  while (std::getline(in, line)) {
    std::istringstream iss(line);
    char ch;
    std::vector<int32_t> vec;
    int32_t num;

    // Parse vector part
    iss >> ch;  // '['
    while (iss >> num) {
      vec.push_back(num);
      iss >> ch;  // ',' or ']'
      if (ch == ']')
        break;
    }

    std::string colon;
    double value;
    iss >> colon >> value;

    data[vec] = value;
  }

  return data;
}

// Dump output sorted by value descending
void dumpSortedByValue(const std::map<std::vector<int32_t>, double>& ret, const std::string& filename)
{
  std::vector<std::pair<std::vector<int32_t>, double>> sorted_entries(ret.begin(), ret.end());

  std::sort(sorted_entries.begin(), sorted_entries.end(), [](const auto& a, const auto& b) {
    if (a.second != b.second)
      return a.second > b.second;
    return a.first > b.first;
  });

  std::ofstream out(filename);
  if (!out) {
    std::cerr << "Error: Cannot open file " << filename << " for writing.\n";
    return;
  }

  for (const auto& pair : sorted_entries) {
    out << "[";
    for (size_t i = 0; i < pair.first.size(); ++i) {
      out << pair.first[i];
      if (i < pair.first.size() - 1)
        out << ", ";
    }
    out << "] : " << pair.second << "\n";
  }

  out.close();
  std::cout << "Dumped to file: " << filename << std::endl;
}

int main()
{
  const std::string input_filename = "inconsistent.txt";
  const std::string output_filename = "consistent.txt";

  std::map<std::vector<int32_t>, double> inconsistent = read_input(input_filename);
  std::map<std::vector<int32_t>, double> consistent;

  double max_diff = 0.0;
  std::vector<int32_t> max_vec1, max_vec2;
  for (const auto& pair : inconsistent) {
    const std::vector<int32_t>& vec = pair.first;
    std::vector<std::vector<int32_t>> orbit = generate_orbit(vec);

    std::vector<double> values;
    for (const auto& o : orbit) {
      if (inconsistent.find(o) == inconsistent.end()) {
        std::cout << "para\n";
      }
      values.push_back(inconsistent[o]);
    }

    for (size_t i = 0; i < values.size(); ++i) {
      for (size_t j = i + 1; j < values.size(); ++j) {
        double diff = std::abs(values[i] - values[j]);
        if (diff > max_diff) {
          max_diff = diff;
          max_vec1 = orbit[i];
          max_vec2 = orbit[j];
        }
      }
    }

    double sum = std::accumulate(values.begin(), values.end(), 0.0);
    double avg = sum / static_cast<double>(values.size());
    consistent[vec] = avg;
  }

  dumpSortedByValue(consistent, output_filename);
  dumpSortedByValue(inconsistent, "ppp");

  std::cout << "Maximum difference in any orbit: " << max_diff << "\n";
  std::cout << "Between elements:\n[";
  for (size_t i = 0; i < max_vec1.size(); ++i) {
    std::cout << max_vec1[i];
    if (i < max_vec1.size() - 1)
      std::cout << ", ";
  }
  std::cout << "] and [";
  for (size_t i = 0; i < max_vec2.size(); ++i) {
    std::cout << max_vec2[i];
    if (i < max_vec2.size() - 1)
      std::cout << ", ";
  }
  std::cout << "]\n";
  return 0;
}
