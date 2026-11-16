use std::{hint::black_box, time::Instant};
use vello_cpu::{Pixmap, fine::{FineKernel,U8Kernel},region::Region};
use vello_common::{fearless_simd::{Level,dispatch},geometry::RectU16};
fn main() {
    let args:Vec<String>=std::env::args().collect();
    let width:u16=args[1].parse().unwrap();
    let iterations:u64=args[2].parse().unwrap();
    let mut pixmap=Pixmap::new(width,4);
    let mut view=pixmap.as_mut();
    let mut region=Region::new(&mut view,RectU16::new(0,0,width,4));
    let source:Vec<u8>=(0..usize::from(width)*16).map(|i|(i*7+13) as u8).collect();
    let mut scratch=vec![0_u8;source.len()];
    dispatch!(Level::try_detect().unwrap_or(Level::baseline()),simd=>{
        U8Kernel::pack(simd,&source,usize::from(width),&mut region);
        for sample in 0..2 {
            let start=Instant::now();
            for _ in 0..iterations {
                U8Kernel::unpack(simd,black_box(&mut region),black_box(usize::from(width)),black_box(&mut scratch));
            }
            let elapsed=start.elapsed();
            black_box(&scratch);
            assert_eq!(scratch,source);
            if sample==1 { println!("{}",elapsed.as_nanos() as f64/iterations as f64); }
        }
    });
}
