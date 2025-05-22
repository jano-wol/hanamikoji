#include <iostream>
#include <fstream>
#include <vector>
#include <map>
#include <string>
#include <sstream>
#include <algorithm>
#include <numeric>

// Generate all 12 permutations of the vector based on 3! × 2! symmetries
std::vector<std::vector<int32_t>> generate_orbit(const std::vector<int32_t>& v) {
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
std::map<std::vector<int32_t>, double> read_input(const std::string& filename) {
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
    iss >> ch; // '['
    while (iss >> num) {
      vec.push_back(num);
      iss >> ch; // ',' or ']'
      if (ch == ']') break;
    }

    std::string colon;
    double value;
    iss >> colon >> value;

    data[vec] = value;
  }

  return data;
}

// Dump output sorted by value descending
void dumpSortedByValue(const std::map<std::vector<int32_t>, double>& ret, const std::string& filename) {
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

int main() {
  const std::string input_filename = "inconsistent.txt";
  const std::string output_filename = "consistent.txt";

  std::map<std::vector<int32_t>, double> inconsistent = read_input(input_filename);
  std::map<std::vector<int32_t>, double> consistent;

  for (const auto& pair : inconsistent) {
    const std::vector<int32_t>& vec = pair.first;
    std::vector<std::vector<int32_t>> orbit = generate_orbit(vec);

    double sum = 0.0;
    for (const auto& o : orbit) {
      if (inconsistent.find(o) == inconsistent.end())
      {
        std::cout << "para\n";
      }
      sum += inconsistent[o];
    }

    double avg = sum / static_cast<double>(orbit.size());
    consistent[vec] = avg;
  }

  dumpSortedByValue(consistent, output_filename);
  dumpSortedByValue(inconsistent, "ppp");
  return 0;
}

