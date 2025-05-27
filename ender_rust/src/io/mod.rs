use std::{ffi::CStr, fs, fs::File, io, io::Write, path::Path, slice};

pub fn write_file_with_dirs(path: &str, data: &[u8]) -> io::Result<()> {
    let path = Path::new(path);

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)?; // ✅ creates intermediate dirs if missing
    }

    let mut file = File::create(path)?;
    file.write_all(data)?;
    Ok(())
}

#[no_mangle]
pub extern "C" fn write_file(path: *const u8, data: *const u8, len: usize) {
    let path = unsafe { CStr::from_ptr(path as *const i8) }.to_str().unwrap();
    let data = unsafe { std::slice::from_raw_parts(data, len) };
    //println!("Got path {} with len {}", path, len);

    // HAHA NO ERROR MESSAGE FOR YOU
    // Bad idea :(
    if false {
        let _ = write_file_with_dirs(path, data);
    } else {
        match write_file_with_dirs(path, data) {
            Ok(_) => {}
            Err(e) => eprintln!("Failed to write {}: {}", path, e),
        }
    }
}

#[no_mangle] // Parallizing has a 20-50% performance boost
pub extern "C" fn write_files(
    paths: *const *const u8,
    data: *const *const u8,
    lens: *const usize,
    count: usize,
) {
    // SAFETY: Copy pointers and lengths into safe Rust vectors first
    let paths_raw = unsafe { slice::from_raw_parts(paths, count) };
    let data_raw = unsafe { slice::from_raw_parts(data, count) };
    let lens_raw = unsafe { slice::from_raw_parts(lens, count) };

    // Convert raw pointers to owned safe slices and Strings upfront
    let files: Vec<(String, Vec<u8>)> = (0..count)
        .map(|i| {
            // Convert path C string to Rust String
            let path = unsafe {
                CStr::from_ptr(paths_raw[i] as *const i8)
                    .to_str()
                    .expect("Invalid UTF-8 in path")
                    .to_owned()
            };

            // Copy file bytes into owned Vec<u8>
            let bytes =
                unsafe { slice::from_raw_parts(data_raw[i], lens_raw[i]) }
                    .to_vec();

            (path, bytes)
        })
        .collect();

    // Now parallelize over safe owned data
    files.into_par_iter().for_each(|(path, bytes)| {
        if false {
            let _ = write_file_with_dirs(&path, &bytes);
        } else {
            match write_file_with_dirs(&path, &bytes) {
                Ok(_) => {}
                Err(e) => eprintln!("Failed to write {}: {}", path, e),
            }
        }
    });
}

// #[no_mangle]
// pub extern "C" fn write_files(
//     paths: *const *const u8,
//     data: *const *const u8,
//     lens: *const usize,
//     count: usize,
// ) {
//     let paths = unsafe { slice::from_raw_parts(paths, count) };
//     let data = unsafe { slice::from_raw_parts(data, count) };
//     let lens = unsafe { slice::from_raw_parts(lens, count) };

//     for i in 0..count {
//         let path =
//             unsafe { CStr::from_ptr(paths[i] as *const i8) }.to_str().unwrap();
//         let bytes = unsafe { slice::from_raw_parts(data[i], lens[i]) };
//         if false {
//             let _ = write_file_with_dirs(path, bytes);
//         } else {
//             match write_file_with_dirs(path, bytes) {
//                 Ok(_) => {}
//                 Err(e) => eprintln!("Failed to write {}: {}", path, e),
//             }
//         }
//     }
// }

use rayon::prelude::*;

/// Recursively delete a directory and all its contents in parallel
pub fn remove_dir_all_parallel<P: AsRef<Path>>(path: P) -> io::Result<()> {
    let path = path.as_ref();

    if !path.exists() {
        return Ok(()); // nothing to do
    }

    if path.is_dir() {
        // Collect entries to a Vec first
        let entries: Vec<_> =
            fs::read_dir(path)?.filter_map(Result::ok).collect();

        // Recursively delete entries in parallel
        entries.par_iter().try_for_each(|entry| {
            let entry_path = entry.path();
            if entry_path.is_dir() {
                remove_dir_all_parallel(&entry_path)
            } else {
                fs::remove_file(&entry_path)
            }
        })?;

        // Remove the now-empty directory
        fs::remove_dir(path)?;
    } else {
        fs::remove_file(path)?;
    }

    Ok(())
}
use std::os::raw::c_char;

#[no_mangle]
pub extern "C" fn delete_path_parallel(path: *const c_char) -> i32 {
    let c_str = unsafe { CStr::from_ptr(path) };
    let path_str = match c_str.to_str() {
        Ok(s) => s,
        Err(_) => return -1,
    };

    match remove_dir_all_parallel(path_str) {
        Ok(_) => -2,
        Err(_) => -3,
    }
}

mod specialized;
pub use specialized::*;
