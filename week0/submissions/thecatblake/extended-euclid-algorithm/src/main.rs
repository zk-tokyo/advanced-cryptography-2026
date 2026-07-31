use std::{env, process};

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 4 {
        println!("The number of arguments must be 2, the x and y.");
        process::exit(1);
    }

    let a: i32 = args[1]
        .parse()
        .expect("The first argument must be an integer.");

    let b: i32 = args[2]
        .parse()
        .expect("The second argument must be an integer.");

    let n: i32 = args[3]
        .parse()
        .expect("The third argument must be an integer.");

    let (x, y) = extended_euclidean_algorithm(a, b, n);

    println!("x = {}, y = {}", x, y);
}

fn extended_euclidean_algorithm(mut a: i32, mut b: i32, n: i32) -> (i32, i32) {
    if a < b {
        let (s, t) = extended_euclidean_algorithm(b, a, n);
        return (t, s);
    }

    let mut s2: i32 = 1; // s_{n-2}
    let mut t2: i32 = 0; // t_{n-2}
    let mut s1: i32 = 0;
    let mut t1: i32 = 1;
    let mut tmp: i32;

    while b != 0 {
        let q = a / b;
        let r = a % b;

        tmp = s2;
        s2 = s1;
        s1 = tmp - s1 * q;

        tmp = t2;
        t2 = t1;
        t1 = tmp - t1 * q;
        a = b;
        b = r;
    }

    if n % a != 0 {
        panic!("No solution!");
    }

    let k = n / a;
    (s2 * k, t2 * k)
}
