use serde::Serialize;

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct HostCapabilities {
    desktop_host: bool,
    arbitrary_shell: bool,
    registered_tools: bool,
}

#[tauri::command]
fn host_capabilities() -> HostCapabilities {
    HostCapabilities {
        desktop_host: true,
        arbitrary_shell: false,
        registered_tools: false,
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![host_capabilities])
        .run(tauri::generate_context!())
        .expect("error while running Case Bible Workbench");
}

