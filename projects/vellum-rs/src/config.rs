use serde::Deserialize;
use std::fs;
use std::path::PathBuf;

#[derive(Debug, Deserialize, Clone)]
pub struct Config {
    #[serde(default = "default_ollama_url")]
    pub ollama_url: String,
    #[serde(default = "default_model")]
    pub model: String,
    #[serde(default = "default_autosave_seconds")]
    pub autosave_seconds: u64,
    #[serde(default = "default_export")]
    #[allow(dead_code)]
    pub default_export: String,
}

fn default_ollama_url() -> String {
    "http://localhost:11434".to_string()
}

fn default_model() -> String {
    "qwen3:4b".to_string()
}

fn default_autosave_seconds() -> u64 {
    30
}

fn default_export() -> String {
    "epub".to_string()
}

impl Default for Config {
    fn default() -> Self {
        Self {
            ollama_url: default_ollama_url(),
            model: default_model(),
            autosave_seconds: default_autosave_seconds(),
            default_export: default_export(),
        }
    }
}

pub fn config_path() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    home.join(".vellum-rs").join("config.toml")
}

pub fn data_dir() -> PathBuf {
    let home = dirs::home_dir().unwrap_or_else(|| PathBuf::from("."));
    home.join(".vellum-rs")
}

pub fn load_config() -> Config {
    let path = config_path();
    if path.exists() {
        match fs::read_to_string(&path) {
            Ok(content) => match toml::from_str(&content) {
                Ok(cfg) => return cfg,
                Err(e) => eprintln!("Warning: bad config at {:?}: {}", path, e),
            },
            Err(e) => eprintln!("Warning: could not read config: {}", e),
        }
    }
    Config::default()
}
