package main

import (
    "fmt"
    "io"
    "os"
    "strconv"
    "strings"
)

func main() {
    data, err := io.ReadAll(os.Stdin)
    if err != nil { os.Exit(2) }
    tokens := strings.Fields(string(data))
    if len(tokens) == 0 { os.Exit(2) }
    n, err := strconv.Atoi(tokens[0])
    if err != nil || n < 0 || n > 64 || len(tokens) != n + 1 { os.Exit(2) }
    var sum, squares int
    for i := 0; i < n; i++ {
        x, err := strconv.Atoi(tokens[i + 1])
        if err != nil || x < -1000 || x > 1000 { os.Exit(2) }
        sum += x
        squares += x * x
    }
    fmt.Printf("%d %d %d\n", n, sum, squares)
}
