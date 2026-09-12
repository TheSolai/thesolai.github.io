use serde::{Deserialize, Serialize};
use std::fs;
use std::path::PathBuf;
use std::sync::Mutex;
use std::time::Duration;
use tauri::{Manager, State};

// ── Config ────────────────────────────────────────────────────────────────────

fn data_dir() -> PathBuf {
    dirs::data_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("vellum")
}

fn config_path() -> PathBuf {
    dirs::config_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("vellum")
        .join("config.toml")
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    #[serde(default = "default_ollama_url")]
    pub ollama_url: String,
    #[serde(default = "default_model")]
    pub model: String,
    #[serde(default = "default_autosave_seconds")]
    pub autosave_seconds: u64,
    #[serde(default = "default_author")]
    pub author: String,
}

fn default_ollama_url() -> String {
    "http://localhost:11434".to_string()
}
fn default_model() -> String {
    // qwen2.5:3b: small, fast, reliable at prose edits.
    // (qwen3:* models use thinking tokens and often return empty
    // unless num_predict is huge; gemma4:12b is multimodal.)
    "qwen2.5:3b".to_string()
}
fn default_autosave_seconds() -> u64 {
    30
}
fn default_author() -> String {
    "Annemarie Lee".to_string()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            ollama_url: default_ollama_url(),
            model: default_model(),
            autosave_seconds: default_autosave_seconds(),
            author: default_author(),
        }
    }
}

fn load_config_from_disk() -> Config {
    let path = config_path();
    if path.exists() {
        match fs::read_to_string(&path) {
            Ok(content) => match toml::from_str(&content) {
                Ok(cfg) => return cfg,
                Err(e) => eprintln!("vellum: bad config at {:?}: {}", path, e),
            },
            Err(e) => eprintln!("vellum: could not read config {:?}: {}", path, e),
        }
    }
    Config::default()
}

fn save_config_to_disk(cfg: &Config) -> Result<(), String> {
    let path = config_path();
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    let s = toml::to_string_pretty(cfg).map_err(|e| e.to_string())?;
    fs::write(&path, s).map_err(|e| e.to_string())?;
    Ok(())
}

// ── Ollama helpers ────────────────────────────────────────────────────────────

#[derive(Debug, Deserialize)]
struct OllamaResponse {
    response: String,
}

async fn check_ollama_at(url: &str) -> bool {
    let client = match reqwest::Client::builder()
        .timeout(Duration::from_secs(5))
        .build()
    {
        Ok(c) => c,
        Err(_) => return false,
    };

    let tags_url = format!("{}/api/tags", url.trim_end_matches('/'));
    match client.get(&tags_url).send().await {
        Ok(resp) => resp.status().is_success(),
        Err(_) => false,
    }
}

const PROSE_FIX_PROMPT: &str =
    "You are a prose editor. Improve the following text: fix grammar, remove repetition, strengthen weak verbs, keep the writer's voice. Return ONLY the improved text, no commentary.\n\n";

const PROSE_EXTEND_PROMPT: &str =
    "You are a creative writing assistant. Continue the following text naturally, extending the ideas already present. Match the tone and style. Return ONLY the continuation, no commentary.\n\n";

async fn ollama_generate(
    prompt_prefix: &str,
    body_text: &str,
    cfg: &Config,
    temperature: f32,
    num_predict: u32,
) -> Result<String, String> {
    let client = reqwest::Client::builder()
        .timeout(Duration::from_secs(60))
        .build()
        .map_err(|e| e.to_string())?;

    // Thinking-style models (qwen3, deepseek-r1) eat hundreds of tokens
    // on internal reasoning before producing output. Give them room by
    // default; small instruct models are unaffected.
    let effective_predict = if cfg.model.contains("qwen3")
        || cfg.model.contains("deepseek-r1")
        || cfg.model.contains("qwq")
    {
        num_predict.max(1500)
    } else {
        num_predict
    };

    let body = serde_json::json!({
        "model": cfg.model,
        "prompt": format!("{}{}", prompt_prefix, body_text),
        "stream": false,
        "options": {
            "temperature": temperature,
            "num_predict": effective_predict
        }
    });

    let api_url = format!("{}/api/generate", cfg.ollama_url.trim_end_matches('/'));

    let resp = client
        .post(&api_url)
        .json(&body)
        .send()
        .await
        .map_err(|e| {
            if e.is_connect() || e.is_timeout() {
                "Ollama unreachable — is `ollama serve` running?".to_string()
            } else {
                format!("request failed: {}", e)
            }
        })?;

    if !resp.status().is_success() {
        return Err(format!("Ollama returned status {}", resp.status()));
    }

    let parsed: OllamaResponse = resp
        .json()
        .await
        .map_err(|e| format!("failed to parse Ollama response: {}", e))?;
    Ok(parsed.response.trim().to_string())
}

// ── Commands ──────────────────────────────────────────────────────────────────

#[tauri::command]
async fn get_config(state: State<'_, Mutex<Config>>) -> Result<Config, String> {
    Ok(state.lock().map_err(|e| e.to_string())?.clone())
}

#[tauri::command]
async fn update_config(
    state: State<'_, Mutex<Config>>,
    ollama_url: Option<String>,
    model: Option<String>,
    autosave_seconds: Option<u64>,
    author: Option<String>,
) -> Result<Config, String> {
    let new_cfg = {
        let mut cfg = state.lock().map_err(|e| e.to_string())?;
        if let Some(u) = ollama_url {
            cfg.ollama_url = u;
        }
        if let Some(m) = model {
            cfg.model = m;
        }
        if let Some(s) = autosave_seconds {
            cfg.autosave_seconds = s;
        }
        if let Some(a) = author {
            cfg.author = a;
        }
        cfg.clone()
    };
    save_config_to_disk(&new_cfg)?;
    Ok(new_cfg)
}

#[tauri::command]
async fn check_ollama(state: State<'_, Mutex<Config>>) -> Result<bool, String> {
    let url = state
        .lock()
        .map_err(|e| e.to_string())?
        .ollama_url
        .clone();
    Ok(check_ollama_at(&url).await)
}

#[tauri::command]
async fn fix_prose(
    text: String,
    state: State<'_, Mutex<Config>>,
) -> Result<String, String> {
    let cfg = state.lock().map_err(|e| e.to_string())?.clone();
    ollama_generate(PROSE_FIX_PROMPT, &text, &cfg, 0.35, 600).await
}

#[tauri::command]
async fn extend_prose(
    text: String,
    hint: String,
    state: State<'_, Mutex<Config>>,
) -> Result<String, String> {
    let cfg = state.lock().map_err(|e| e.to_string())?.clone();
    let input = if hint.is_empty() {
        text.clone()
    } else {
        format!("{}\n\nHint: {}", text, hint)
    };
    ollama_generate(PROSE_EXTEND_PROMPT, &input, &cfg, 0.4, 800).await
}

#[derive(Serialize)]
struct DraftLoad {
    text: String,
    filename: Option<String>,
}

#[tauri::command]
async fn load_draft() -> Result<DraftLoad, String> {
    let dir = data_dir();
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;

    // Find most recent .draft file
    let entries = fs::read_dir(&dir).map_err(|e| e.to_string())?;
    let mut drafts: Vec<_> = entries
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().and_then(|s| s.to_str()) == Some("draft"))
        .collect();
    drafts.sort_by_key(|e| std::cmp::Reverse(e.metadata().and_then(|m| m.modified()).ok()));

    if let Some(entry) = drafts.first() {
        let path = entry.path();
        let text = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        // path is ".../<name>.draft" — file_stem returns "<name>.draft"
        // strip the .draft suffix to get the original filename.
        let filename = path
            .file_stem()
            .and_then(|s| s.to_str())
            .map(|s| s.strip_suffix(".draft").unwrap_or(s).to_string());
        Ok(DraftLoad { text, filename })
    } else {
        Ok(DraftLoad {
            text: String::new(),
            filename: None,
        })
    }
}

#[tauri::command]
async fn save_file(text: String, filename: Option<String>) -> Result<String, String> {
    let dir = data_dir();
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;

    let name = filename.unwrap_or_else(|| "untitled".to_string());
    let path = dir.join(format!("{}.txt", name));
    fs::write(&path, &text).map_err(|e| e.to_string())?;

    // Mirror to draft for autosave-recovery
    let draft = dir.join(format!("{}.draft", name));
    let _ = fs::write(&draft, &text);

    Ok(name)
}

#[tauri::command]
async fn export_file(
    text: String,
    format: String,
    state: State<'_, Mutex<Config>>,
) -> Result<String, String> {
    let dir = data_dir();
    fs::create_dir_all(&dir).map_err(|e| e.to_string())?;

    let cfg = state.lock().map_err(|e| e.to_string())?.clone();

    match format.as_str() {
        "fountain" => {
            let path = dir.join("export.fountain");
            fs::write(&path, &text).map_err(|e| e.to_string())?;
            Ok(path.to_string_lossy().to_string())
        }
        "epub" => {
            let path = dir.join("export.epub");
            export_epub(&text, &cfg.author, &path)?;
            Ok(path.to_string_lossy().to_string())
        }
        "mobi" => {
            // We don't have a native MOBI writer. Export EPUB alongside and
            // tell the user how to convert (Calibre / Kindle Previewer).
            let epub_path = dir.join("export.epub");
            export_epub(&text, &cfg.author, &epub_path)?;
            Ok(format!(
                "MOBI export requires Calibre or Kindle Previewer. EPUB written to {}. Convert with: ebook-convert export.epub export.mobi",
                epub_path.display()
            ))
        }
        other => Err(format!("Unknown format: {}", other)),
    }
}

// ── EPUB export ───────────────────────────────────────────────────────────────

fn xml_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&apos;")
}

fn split_chapters(text: &str) -> Vec<(String, String)> {
    // Split on blank-line-separated sections.
    // A section whose first line starts with "# " is treated as a titled chapter.
    let sections: Vec<&str> = text.split("\n\n").collect();
    let mut out: Vec<(String, String)> = Vec::new();

    for (i, section) in sections.iter().enumerate() {
        let trimmed = section.trim();
        if trimmed.is_empty() {
            continue;
        }
        let first_line = trimmed.lines().next().unwrap_or("").trim();
        if first_line.starts_with("# ") {
            let title = first_line.trim_start_matches("# ").trim().to_string();
            let body = trimmed
                .lines()
                .skip(1)
                .collect::<Vec<_>>()
                .join("\n")
                .trim()
                .to_string();
            out.push((title, body));
        } else {
            out.push((format!("Chapter {}", i + 1), trimmed.to_string()));
        }
    }

    if out.is_empty() {
        out.push(("Untitled".to_string(), text.to_string()));
    }
    out
}

fn format_paragraphs(text: &str) -> String {
    text.lines()
        .map(|line| {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                String::from("<p>&nbsp;</p>")
            } else {
                format!("<p>{}</p>", xml_escape(trimmed))
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn uuid_v4() -> String {
    // Pseudo-UUID v4 from system time + PID. Not cryptographic but
    // unique enough for an EPUB identifier on a single machine.
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let pid = std::process::id() as u128;
    let combined: u128 = now.wrapping_mul(0x9E37_79B9_7F4A_7C15).wrapping_add(pid);
    let mut bytes = combined.to_be_bytes();
    // RFC 4122: set version 4 and variant bits.
    bytes[6] = (bytes[6] & 0x0F) | 0x40; // top nibble = 4 (version 4)
    bytes[8] = (bytes[8] & 0x3F) | 0x80; // top nibble = 8..B (variant 10xx)
    format!(
        "{:02x}{:02x}{:02x}{:02x}-{:02x}{:02x}-4{:x}{:02x}-{:x}{:x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}",
        bytes[0], bytes[1], bytes[2], bytes[3],
        bytes[4], bytes[5],
        bytes[6] & 0x0F,
        bytes[7],
        bytes[8] >> 4,
        bytes[8] & 0x0F,
        bytes[9],
        bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15],
    )
}

fn export_epub(text: &str, author: &str, path: &PathBuf) -> Result<(), String> {
    use std::io::Write;
    use zip::write::SimpleFileOptions;

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    let file = fs::File::create(path).map_err(|e| e.to_string())?;
    let mut zip = zip::ZipWriter::new(file);

    let stored = SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Stored);
    let deflated = SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated);

    // 1. mimetype — must be first and uncompressed
    zip.start_file("mimetype", stored.clone())
        .map_err(|e| e.to_string())?;
    zip.write_all(b"application/epub+zip")
        .map_err(|e| e.to_string())?;

    // 2. META-INF/container.xml
    zip.start_file("META-INF/container.xml", deflated.clone())
        .map_err(|e| e.to_string())?;
    zip.write_all(
        br#"<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"#,
    )
    .map_err(|e| e.to_string())?;

    // 3. Chapter content
    let chapters = split_chapters(text);
    let book_id = uuid_v4();
    let title = path
        .file_stem()
        .and_then(|s| s.to_str())
        .unwrap_or("Vellum Export")
        .to_string();

    // Build chapter XHTMLs first so we can write content.opf/nav.xhtml with correct refs.
    let mut manifest_items = String::new();
    let mut spine_items = String::new();
    let mut nav_items = String::new();

    for (i, (ch_title, ch_body)) in chapters.iter().enumerate() {
        let ch_id = format!("chapter{}", i + 1);
        let filename = format!("{}.xhtml", ch_id);

        manifest_items.push_str(&format!(
            "    <item id=\"{}\" href=\"{}\" media-type=\"application/xhtml+xml\"/>\n",
            ch_id, filename
        ));
        spine_items.push_str(&format!("    <itemref idref=\"{}\"/>\n", ch_id));
        nav_items.push_str(&format!(
            "    <li><a href=\"{}\">{}</a></li>\n",
            filename,
            xml_escape(ch_title)
        ));

        let ch_xhtml = format!(
            r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{title}</title>
  <style>
    body {{ font-family: Georgia, serif; margin: 1em 1.5em; line-height: 1.6; }}
    h1 {{ font-size: 1.4em; margin: 0.6em 0 0.4em; }}
    p {{ margin: 0.5em 0; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
{body}
</body>
</html>"#,
            title = xml_escape(ch_title),
            body = format_paragraphs(ch_body),
        );

        zip.start_file(format!("OEBPS/{}", filename), deflated.clone())
            .map_err(|e| e.to_string())?;
        zip.write_all(ch_xhtml.as_bytes())
            .map_err(|e| e.to_string())?;
    }

    // 4. content.opf
    let content_opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:{book_id}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>en</dc:language>
    <meta name="generator" content="vellum-rs"/>
  </metadata>
  <manifest>
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>
{manifest}
  </manifest>
  <spine>
    <itemref idref="nav"/>
{spine}
  </spine>
</package>"#,
        book_id = book_id,
        title = xml_escape(&title),
        author = xml_escape(author),
        manifest = manifest_items.trim_end(),
        spine = spine_items.trim_end(),
    );
    zip.start_file("OEBPS/content.opf", deflated.clone())
        .map_err(|e| e.to_string())?;
    zip.write_all(content_opf.as_bytes())
        .map_err(|e| e.to_string())?;

    // 5. nav.xhtml
    let nav = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>Contents</title></head>
<body>
  <nav epub:type="toc"><h1>Contents</h1><ol>
{nav_items}  </ol></nav>
</body>
</html>"#,
        nav_items = nav_items
    );
    zip.start_file("OEBPS/nav.xhtml", deflated.clone())
        .map_err(|e| e.to_string())?;
    zip.write_all(nav.as_bytes())
        .map_err(|e| e.to_string())?;

    zip.finish().map_err(|e| e.to_string())?;
    Ok(())
}

// ── App Entry ────────────────────────────────────────────────────────────────

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    // Ensure dirs exist
    let _ = fs::create_dir_all(data_dir());
    let cfg_path = config_path();
    if let Some(parent) = cfg_path.parent() {
        let _ = fs::create_dir_all(parent);
    }

    let config = load_config_from_disk();

    tauri::Builder::default()
        .manage(Mutex::new(config))
        .invoke_handler(tauri::generate_handler![
            get_config,
            update_config,
            check_ollama,
            fix_prose,
            extend_prose,
            load_draft,
            save_file,
            export_file,
        ])
        .setup(|app| {
            if let Some(window) = app.get_webview_window("main") {
                let _ = window.set_title("Vellum");
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

// ── Tests ─────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn config_default_has_sensible_ollama() {
        let c = Config::default();
        assert_eq!(c.ollama_url, "http://localhost:11434");
        assert!(!c.model.is_empty());
        assert!(c.autosave_seconds > 0);
    }

    #[test]
    fn config_roundtrips_through_toml() {
        let original = Config {
            ollama_url: "http://example.com:9999".to_string(),
            model: "llama3:8b".to_string(),
            autosave_seconds: 60,
            author: "Test Author".to_string(),
        };
        let s = toml::to_string(&original).unwrap();
        let parsed: Config = toml::from_str(&s).unwrap();
        assert_eq!(parsed.ollama_url, "http://example.com:9999");
        assert_eq!(parsed.model, "llama3:8b");
        assert_eq!(parsed.autosave_seconds, 60);
        assert_eq!(parsed.author, "Test Author");
    }

    #[test]
    fn xml_escape_handles_all_specials() {
        assert_eq!(xml_escape("a & b"), "a &amp; b");
        assert_eq!(xml_escape("<b>"), "&lt;b&gt;");
        assert_eq!(xml_escape("\"hi\""), "&quot;hi&quot;");
        assert_eq!(xml_escape("it's"), "it&apos;s");
    }

    #[test]
    fn split_chapters_titles_with_hash() {
        let text = "# One\nFirst chapter body.\n\n# Two\nSecond chapter body.";
        let chapters = split_chapters(text);
        assert_eq!(chapters.len(), 2);
        assert_eq!(chapters[0].0, "One");
        assert!(chapters[0].1.contains("First chapter"));
        assert_eq!(chapters[1].0, "Two");
        assert!(chapters[1].1.contains("Second chapter"));
    }

    #[test]
    fn split_chapters_uses_generic_names_when_no_heading() {
        let text = "First paragraph.\n\nSecond paragraph.";
        let chapters = split_chapters(text);
        assert_eq!(chapters.len(), 2);
        assert_eq!(chapters[0].0, "Chapter 1");
        assert!(chapters[0].1.contains("First paragraph"));
    }

    #[test]
    fn split_chapters_falls_back_to_untitled_for_empty() {
        let chapters = split_chapters("");
        assert_eq!(chapters.len(), 1);
        assert_eq!(chapters[0].0, "Untitled");
    }

    #[test]
    fn uuid_v4_format_is_valid() {
        let u = uuid_v4();
        // 8-4-4-4-12 hex digits
        assert_eq!(u.len(), 36);
        assert_eq!(u.chars().nth(14), Some('4')); // version 4 marker
    }
}
