use std::ffi::CStr;
use std::fs;
use std::os::raw::c_char;
use std::path::{Path, PathBuf};
use walkdir::WalkDir;

/// Replace any part named "builtin" with the given mod_id
fn replace_builtin_with_mod_id(path: &Path, mod_id: &str) -> PathBuf {
    PathBuf::from_iter(path.iter().map(|part| {
        if part == "builtin" {
            std::ffi::OsString::from(mod_id)
        } else {
            part.to_os_string()
        }
    }))
}

#[no_mangle]
pub extern "C" fn copy_and_rename_builtin_ffi(
    source: *const c_char,
    destination: *const c_char,
    mod_id: *const c_char,
) -> i32 {
    // Safety: Ensure valid C strings
    let source_cstr = unsafe { CStr::from_ptr(source) };
    let dest_cstr = unsafe { CStr::from_ptr(destination) };
    let mod_id_cstr = unsafe { CStr::from_ptr(mod_id) };

    let source_str = match source_cstr.to_str() {
        Ok(s) => s,
        Err(_) => return 1,
    };
    let dest_str = match dest_cstr.to_str() {
        Ok(s) => s,
        Err(_) => return 1,
    };
    let mod_id_str = match mod_id_cstr.to_str() {
        Ok(s) if !s.trim().is_empty() => s,
        _ => return 1,
    };

    let source_path = Path::new(source_str);
    let dest_path = Path::new(dest_str);

    if !source_path.exists() {
        return 2;
    }

    let walker = WalkDir::new(source_path).into_iter();

    for entry in walker {
        match entry {
            Ok(entry) => {
                let path = entry.path();

                if path.is_dir() {
                    continue;
                }

                // Get relative path
                let rel_path = match path.strip_prefix(source_path) {
                    Ok(p) => p,
                    Err(_) => return 2,
                };

                let target_path = dest_path
                    .join(replace_builtin_with_mod_id(rel_path, mod_id_str));

                // Create parent directories
                if let Some(parent) = target_path.parent() {
                    if let Err(_) = fs::create_dir_all(parent) {
                        return 2;
                    }
                }

                // Copy file
                if let Err(_) = fs::copy(path, &target_path) {
                    return 2;
                }
            }
            Err(_) => return 2,
        }
    }

    0 // success
}
