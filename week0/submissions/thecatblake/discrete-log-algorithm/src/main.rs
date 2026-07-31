use std::{env, process};

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() != 4 {
        println!("The number of arguments must be 2, the x and y.");
        process::exit(1);
    }

    let a: u32 = args[1]
        .parse()
        .expect("The first argument must be an integer.");

    let b: u32 = args[2]
        .parse()
        .expect("The second argument must be an integer.");

    let n: u32 = args[3]
        .parse()
        .expect("The third argument must be an integer.");

    if let Some(k) = group_mul_dlp_solve(a, b, n) {
        println!("log_b(a) = {}", k);
    } else {
        println!("No solution!");
    }
}

fn group_mul_inv(m: u32, n: u32) -> u32 {
    let n32 = n as i32;
    let (s, _) = extended_euclidean_algorithm(m as i32, n as i32, 1);
    (((s % n32) + n32) % n32) as u32
}

// log_b{a}
fn group_mul_dlp_solve(a: u32, b: u32, n: u32) -> Option<u32> {
    let m = (n as f32).sqrt().ceil() as u32;
    
    let mut table = vec![0; m as usize];

    table[0] = 1;
    for i in 1..m {
        table[i as usize] =
            table[(i - 1) as usize] * b % n;
    }

    let mut tmp = a;
    let b_inv = group_mul_inv(b, n);
    let b_pow = mod_pow(b_inv, m, n);
    for i in 0..m {
        for j in 0..m {
            if table[j as usize] == tmp % n {
                return Some(i * m + j);
            }
        }
        tmp = tmp * b_pow % n;
    }

    None
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

fn mod_pow(
    mut base:u32,
    mut exp:u32,
    modulo:u32
)->u32{

    let mut result=1;

    while exp>0{

        if exp%2==1{
            result=result*base%modulo;
        }

        base=base*base%modulo;
        exp/=2;
    }

    result
}
