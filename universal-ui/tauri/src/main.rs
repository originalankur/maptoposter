// Prevents additional console window on Windows in release builds
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{Manager, Window};
use std::process::{Command, Child};
use std::sync::Mutex;

// Store the server process
struct ServerProcess(Mutex<Option<Child>>);

#[tauri::command]
fn start_server(window: Window) -> Result<String, String> {
    // Start the Python server
    let server = Command::new("python3")
        .arg("universal-ui/runner/run_local.py")
        .arg("--serve")
        .spawn()
        .map_err(|e| format!("Failed to start server: {}", e))?;
    
    // Store the process
    let state: tauri::State<ServerProcess> = window.state();
    *state.0.lock().unwrap() = Some(server);
    
    Ok("Server started".to_string())
}

fn main() {
    tauri::Builder::default()
        .manage(ServerProcess(Mutex::new(None)))
        .invoke_handler(tauri::generate_handler![start_server])
        .setup(|app| {
            // Optionally auto-start server on app launch
            let window = app.get_window("main").unwrap();
            let _ = start_server(window);
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
