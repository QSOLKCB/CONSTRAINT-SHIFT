#include <stdio.h>

int main(void) {
    int n, x, sum = 0, squares = 0;
    if (scanf("%d", &n) != 1 || n < 0 || n > 64) return 2;
    for (int i = 0; i < n; ++i) {
        if (scanf("%d", &x) != 1 || x < -1000 || x > 1000) return 2;
        sum += x;
        squares += x * x;
    }
    printf("%d %d %d\n", n, sum, squares);
    return 0;
}
