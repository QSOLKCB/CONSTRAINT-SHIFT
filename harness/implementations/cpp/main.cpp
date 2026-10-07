#include <iostream>

int main() {
    int n, x, sum = 0, squares = 0;
    if (!(std::cin >> n) || n < 0 || n > 64) return 2;
    for (int i = 0; i < n; ++i) {
        if (!(std::cin >> x) || x < -1000 || x > 1000) return 2;
        sum += x;
        squares += x * x;
    }
    std::cout << n << ' ' << sum << ' ' << squares << '\n';
}
