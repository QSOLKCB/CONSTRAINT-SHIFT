use std::io::{self, Read};

fn main() {
    let mut input = String::new();
    io::stdin().read_to_string(&mut input).unwrap();
    let mut tokens = input.split_ascii_whitespace();
    let n: i32 = tokens.next().unwrap().parse().unwrap();
    assert!((0..=64).contains(&n));
    let mut sum: i32 = 0;
    let mut squares: i32 = 0;
    for _ in 0..n {
        let x: i32 = tokens.next().unwrap().parse().unwrap();
        assert!((-1000..=1000).contains(&x));
        sum += x;
        squares += x * x;
    }
    println!("{} {} {}", n, sum, squares);
}
