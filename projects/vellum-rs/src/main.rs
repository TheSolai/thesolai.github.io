use clap::{Parser, ValueEnum};
use std::path::PathBuf;

mod autofix;
mod config;
mod editor;
mod export;
mod ollama;

#[derive(Parser, Debug)]
#[command(
    name = "vellum-rs",
    about = "A writer's editor with a Tab that makes your words better.",
    version = "0.1.0"
)]
struct Args {
    /// Open an existing file
    file: Option<PathBuf>,

    /// Create a new file with the given name
    #[arg(long)]
    new: Option<String>,

    /// Ollama model to use
    #[arg(long, value_name = "MODEL")]
    model: Option<String>,

    /// Ollama URL
    #[arg(long, value_name = "URL")]
    ollama_url: Option<String>,

    /// Export the file to a format and exit
    #[arg(long, value_name = "FORMAT", value_enum)]
    export: Option<ExportFormat>,
}

#[derive(ValueEnum, Debug, Clone)]
enum ExportFormat {
    Fountain,
    Epub,
    Mobi,
}

fn main() {
    let args = Args::parse();
    let config = config::load_config();

    // Export mode: just export and exit
    if let Some(fmt) = args.export {
        let text = if let Some(ref path) = args.file {
            std::fs::read_to_string(path).expect("Could not read file")
        } else {
            eprintln!("Export requires a file argument.");
            std::process::exit(1);
        };

        let file_stem = args.file.as_ref().map(|p| {
            p.file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("output")
        }).unwrap_or("output");

        let result = match fmt {
            ExportFormat::Fountain => {
                let path = PathBuf::from(file_stem).with_extension("fountain");
                export::export_fountain(&text, &path)
            }
            ExportFormat::Epub => {
                let path = PathBuf::from(file_stem).with_extension("epub");
                export::export_epub(file_stem, "Author", &text, &path)
            }
            ExportFormat::Mobi => {
                let path = PathBuf::from(file_stem).with_extension("mobi");
                export::export_mobi(&text, file_stem, "Author", &path)
            }
        };

        match result {
            Ok(()) => {
                println!("Exported successfully.");
                std::process::exit(0);
            }
            Err(e) => {
                eprintln!("Export failed: {}", e);
                std::process::exit(1);
            }
        }
    }

    // Editor mode
    let (text, filename) = if let Some(name) = args.new {
        // Create new file in ~/.vellum-rs/
        let dir = config::data_dir();
        std::fs::create_dir_all(&dir).expect("Could not create data directory");
        let filename = name.clone();
        let path = dir.join(format!("{}.txt", name));
        if !path.exists() {
            std::fs::write(&path, "").expect("Could not create file");
        }
        let text = std::fs::read_to_string(&path).unwrap_or_default();
        (text, Some(filename))
    } else if let Some(ref path) = args.file {
        let text = std::fs::read_to_string(path).expect("Could not read file");
        let filename = path.file_stem()
            .and_then(|s| s.to_str())
            .map(|s| s.to_string());
        (text, filename)
    } else {
        // No file given — start with empty buffer
        (String::new(), None)
    };

    let mut config = config;
    if let Some(model) = args.model {
        config.model = model;
    }
    if let Some(url) = args.ollama_url {
        config.ollama_url = url;
    }

    // Run the TUI editor
    editor::run_editor(text, filename, config).expect("Editor crashed");
}
