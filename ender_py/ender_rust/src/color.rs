use image::io::Reader as ImageReader;
use std::ffi::CStr;
use std::os::raw::{c_char, c_int};

#[no_mangle]
pub extern "C" fn get_average_color_of_image(
    png_path: *const c_char,
    r: *mut c_int,
    g: *mut c_int,
    b: *mut c_int,
) -> c_int {
    if png_path.is_null() || r.is_null() || g.is_null() || b.is_null() {
        return -1;
    }

    let c_str = unsafe { CStr::from_ptr(png_path) };
    let path = match c_str.to_str() {
        Ok(s) => s,
        Err(_) => return -2,
    };

    let img = match ImageReader::open(path).and_then(|i| Ok(i.decode())) {
        Ok(i) => i.unwrap().to_rgb8(),
        Err(_) => return -3,
    };

    let mut sum_r: u64 = 0;
    let mut sum_g: u64 = 0;
    let mut sum_b: u64 = 0;
    let pixels = img.pixels();
    let count = pixels.len() as u64;

    for pixel in pixels {
        let [pr, pg, pb] = pixel.0;
        sum_r += pr as u64;
        sum_g += pg as u64;
        sum_b += pb as u64;
    }

    if count == 0 {
        return -4;
    }

    unsafe {
        *r = (sum_r / count) as c_int;
        *g = (sum_g / count) as c_int;
        *b = (sum_b / count) as c_int;
    }

    0
}
use std::os::raw::c_float;
#[repr(C)]
pub struct RGB {
    r: c_int,
    g: c_int,
    b: c_int,
}
#[no_mangle]
pub extern "C" fn average_and_find_closest_color_index(
    png_path: *const c_char,
    targets: *const RGB,
    target_count: usize,
    limit: c_float,
) -> c_int {
    // Validate pointers
    if png_path.is_null() || targets.is_null() {
        return -1;
    }

    // Convert C string to Rust string
    let c_str = unsafe { CStr::from_ptr(png_path) };
    let path = match c_str.to_str() {
        Ok(s) => s,
        Err(_) => return -2,
    };

    // Load image and decode
    let img = match ImageReader::open(path).and_then(|i| Ok(i.decode())) {
        Ok(i) => i.unwrap().to_rgb8(),
        Err(_) => return -3,
    };

    let pixels = img.pixels();
    let count = pixels.len() as u64;
    if count == 0 {
        return -4;
    }

    // Calculate average color
    let mut sum_r: u64 = 0;
    let mut sum_g: u64 = 0;
    let mut sum_b: u64 = 0;
    for pixel in pixels {
        let [pr, pg, pb] = pixel.0;
        sum_r += pr as u64;
        sum_g += pg as u64;
        sum_b += pb as u64;
    }

    let avg_r = (sum_r / count) as c_int;
    let avg_g = (sum_g / count) as c_int;
    let avg_b = (sum_b / count) as c_int;

    let targets_slice =
        unsafe { std::slice::from_raw_parts(targets, target_count) };

    // Find closest color index within limit
    let mut min_distance = f32::INFINITY;
    let mut closest_index: Option<usize> = None;

    for (i, target) in targets_slice.iter().enumerate() {
        let dr = (avg_r - target.r) as f32;
        let dg = (avg_g - target.g) as f32;
        let db = (avg_b - target.b) as f32;
        let dist = (dr * dr + dg * dg + db * db).sqrt();

        if dist < min_distance && dist <= limit {
            min_distance = dist;
            closest_index = Some(i);
        }
    }

    match closest_index {
        Some(idx) => idx as c_int,
        None => 1, // no match found within limit
    }
}
