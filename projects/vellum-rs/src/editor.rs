use crate::autofix::{get_current_line, replace_range};
use crate::config::{data_dir, Config};
use crate::export;
use crate::ollama;
use crossterm::event::{Event, KeyCode, KeyModifiers};
use crossterm::execute;
use ratatui::buffer::Buffer;
use ratatui::layout::{Constraint, Direction, Layout, Rect};
use ratatui::style::{Color, Style};
use ratatui::widgets::Widget;
use ratatui::Terminal;
use std::path::PathBuf;
use std::time::{Duration, Instant};
use tokio::sync::mpsc;

pub struct EditorState {
    pub text: String,
    pub filename: Option<String>,
    pub dirty: bool,
    pub word_count_visible: bool,
    pub ollama_online: bool,
    pub fixing: bool,
    pub export_modal: bool,
    pub status_message: Option<String>,
}

impl EditorState {
    pub fn new(text: String, filename: Option<String>) -> Self {
        Self {
            text,
            filename,
            dirty: false,
            word_count_visible: true,
            ollama_online: true,
            fixing: false,
            export_modal: false,
            status_message: None,
        }
    }

    pub fn word_count(&self) -> usize {
        self.text.split_whitespace().count()
    }

    pub fn filename_display(&self) -> &str {
        self.filename.as_deref().unwrap_or("[new file]")
    }

    pub fn save_path(&self) -> PathBuf {
        let dir = data_dir();
        let name = self.filename.clone().unwrap_or_else(|| "untitled".to_string());
        dir.join(format!("{}.txt", name))
    }

    pub fn autosave_path(&self) -> PathBuf {
        let dir = data_dir();
        let name = self.filename.clone().unwrap_or_else(|| "untitled".to_string());
        dir.join(format!("{}.draft", name))
    }
}

struct StatusBar {
    word_count: usize,
    word_count_visible: bool,
    ollama_online: bool,
    filename: String,
    status_message: Option<String>,
}

impl Widget for StatusBar {
    fn render(self, area: Rect, buf: &mut Buffer) {
        let style = Style::default().bg(Color::DarkGray).fg(Color::White);
        buf.set_style(area, style);

        let left = if self.word_count_visible {
            format!(" {} words ", self.word_count)
        } else {
            String::new()
        };

        let ollama_status = if self.ollama_online {
            " ● Ollama"
        } else {
            " ○ Ollama: offline"
        };

        let status = self.status_message.as_deref().unwrap_or("");
        let mid = format!("{}{}", ollama_status, status);
        let right = format!(" {}", self.filename);

        let mut x = area.left();
        for ch in left.chars() {
            if x >= area.right() {
                break;
            }
            buf.set_string(x, area.top(), ch.to_string(), style);
            x += 1;
        }

        x = area.left() + 2;
        for ch in mid.chars() {
            if x >= area.right() {
                break;
            }
            buf.set_string(x, area.top(), ch.to_string(), style);
            x += 1;
        }

        let right_start = area.right().saturating_sub(right.len() as u16);
        x = right_start;
        for ch in right.chars() {
            if x >= area.right() {
                break;
            }
            buf.set_string(x, area.top(), ch.to_string(), style);
            x += 1;
        }
    }
}

struct Overlay {
    text: &'static str,
    fixing: bool,
}

impl Widget for Overlay {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if area.width < 20 || area.height < 3 {
            return;
        }

        let inner = Rect::new(
            area.x + area.width.saturating_sub(20) / 2,
            area.y + area.height.saturating_sub(3) / 2,
            20.min(area.width),
            3.min(area.height),
        );

        let style = Style::default().bg(Color::Black).fg(Color::Cyan);
        let border = Style::default().bg(Color::Black).fg(Color::Cyan);

        for x in inner.x..inner.right() {
            if x == inner.x {
                buf.set_string(x, inner.y, "╭", border);
            } else if x == inner.right() - 1 {
                buf.set_string(x, inner.y, "╮", border);
            } else {
                buf.set_string(x, inner.y, "─", border);
            }
        }
        for x in inner.x..inner.right() {
            if x == inner.x {
                buf.set_string(x, inner.bottom() - 1, "╰", border);
            } else if x == inner.right() - 1 {
                buf.set_string(x, inner.bottom() - 1, "╯", border);
            } else {
                buf.set_string(x, inner.bottom() - 1, "─", border);
            }
        }
        for y in (inner.y + 1)..inner.bottom() - 1 {
            buf.set_string(inner.x, y, "│", border);
            buf.set_string(inner.right() - 1, y, "│", border);
        }
        let text_str = if self.fixing { "✦ Fixing…" } else { self.text };
        let text_len = text_str.len() as u16;
        let text_x = inner.x + (inner.width.saturating_sub(text_len)) / 2;
        let text_y = inner.y + inner.height / 2;
        buf.set_string(text_x, text_y, text_str, style);
    }
}

struct ExportModal;

impl Widget for ExportModal {
    fn render(self, area: Rect, buf: &mut Buffer) {
        if area.width < 30 || area.height < 7 {
            return;
        }

        let inner = Rect::new(
            area.x + area.width.saturating_sub(30) / 2,
            area.y + area.height.saturating_sub(7) / 2,
            30.min(area.width),
            7.min(area.height),
        );

        let bg = Style::default().bg(Color::Blue).fg(Color::White);
        let border = Style::default().bg(Color::Blue).fg(Color::White);

        for x in inner.x..inner.right() {
            buf.set_string(x, inner.y, "─", border);
            buf.set_string(x, inner.bottom() - 1, "─", border);
        }
        for y in (inner.y + 1)..inner.bottom() - 1 {
            buf.set_string(inner.x, y, "│", border);
            buf.set_string(inner.right() - 1, y, "│", border);
        }
        buf.set_string(inner.x, inner.y, "┌", border);
        buf.set_string(inner.right() - 1, inner.y, "┐", border);
        buf.set_string(inner.x, inner.bottom() - 1, "└", border);
        buf.set_string(inner.right() - 1, inner.bottom() - 1, "╘", border);

        buf.set_string(inner.x + 1, inner.y, " Export ", bg);

        let choices = [
            "[f] Fountain (.fountain)",
            "[e] EPUB (.epub)",
            "[m] MOBI (.mobi)",
            "[q] Cancel",
        ];
        let mut y = inner.y + 2;
        for choice in choices {
            buf.set_string(inner.x + 2, y, choice, bg);
            y += 1;
        }
    }
}

fn render_editor(
    terminal: &mut Terminal<ratatui::backend::CrosstermBackend<std::io::Stderr>>,
    state: &EditorState,
) -> Result<(), String> {
    terminal
        .draw(|f| {
            let chunks = Layout::default()
                .direction(Direction::Vertical)
                .constraints([Constraint::Min(1), Constraint::Length(1)])
                .split(f.area());

            let editor_area = chunks[0];
            let status_area = chunks[1];

            StatusBar {
                word_count: state.word_count(),
                word_count_visible: state.word_count_visible,
                ollama_online: state.ollama_online,
                filename: state.filename_display().to_string(),
                status_message: state.status_message.clone(),
            }
            .render(status_area, f.buffer_mut());

            let block = ratatui::widgets::Block::default()
                .title(state.filename_display())
                .title_style(Style::default().fg(Color::White))
                .borders(ratatui::widgets::Borders::ALL)
                .border_style(Style::default().fg(Color::DarkGray));

            let para = ratatui::widgets::Paragraph::new(state.text.as_str())
                .block(block)
                .wrap(ratatui::widgets::Wrap { trim: true });

            para.render(editor_area, f.buffer_mut());

            if state.export_modal {
                ExportModal.render(editor_area, f.buffer_mut());
            } else if state.fixing {
                Overlay {
                    text: "✦ Fixing…",
                    fixing: true,
                }
                .render(editor_area, f.buffer_mut());
            }
        })
        .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn run_editor(
    initial_text: String,
    filename: Option<String>,
    config: Config,
) -> Result<(), String> {
    let mut state = EditorState::new(initial_text, filename);

    let runtime = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()
        .map_err(|e| e.to_string())?;

    state.ollama_online = runtime.block_on(ollama::check_ollama_status(&config.ollama_url));

    let backend = ratatui::backend::CrosstermBackend::new(std::io::stderr());
    let mut terminal = Terminal::new(backend).map_err(|e| e.to_string())?;

    let _ = execute!(std::io::stderr(), crossterm::terminal::EnterAlternateScreen);
    let _ = execute!(std::io::stderr(), crossterm::event::EnableMouseCapture);

    let data_dir = data_dir();
    let _ = std::fs::create_dir_all(&data_dir);

    let autosave_seconds = config.autosave_seconds;
    let mut last_save = Instant::now();
    let mut last_ollama_check = Instant::now();

    // Initial autosave
    let _ = std::fs::write(state.autosave_path(), &state.text);

    'main_loop: loop {
        // Autosave
        if last_save.elapsed() >= Duration::from_secs(autosave_seconds) && state.dirty {
            if std::fs::write(state.autosave_path(), &state.text).is_ok() {
                state.dirty = false;
            }
            last_save = Instant::now();
        }

        // Periodic Ollama check
        if last_ollama_check.elapsed() >= Duration::from_secs(30) {
            let online = runtime.block_on(ollama::check_ollama_status(&config.ollama_url));
            if online != state.ollama_online {
                state.ollama_online = online;
            }
            last_ollama_check = Instant::now();
        }

        render_editor(&mut terminal, &state)?;

        let event = crossterm::event::read().map_err(|e| e.to_string())?;

        if state.export_modal {
            if let Event::Key(key) = event {
                match key.code {
                    KeyCode::Char('f') | KeyCode::Char('F') => {
                        let path = PathBuf::from(state.filename_display()).with_extension("fountain");
                        match export::export_fountain(&state.text, &path) {
                            Ok(()) => state.status_message = Some(format!(" Exported to {:?}", path)),
                            Err(e) => state.status_message = Some(format!(" Export failed: {}", e)),
                        }
                        state.export_modal = false;
                    }
                    KeyCode::Char('e') | KeyCode::Char('E') => {
                        let path = PathBuf::from(state.filename_display()).with_extension("epub");
                        match export::export_epub(state.filename_display(), "Author", &state.text, &path) {
                            Ok(()) => state.status_message = Some(format!(" Exported to {:?}", path)),
                            Err(e) => state.status_message = Some(format!(" Export failed: {}", e)),
                        }
                        state.export_modal = false;
                    }
                    KeyCode::Char('m') | KeyCode::Char('M') => {
                        let path = PathBuf::from(state.filename_display()).with_extension("mobi");
                        match export::export_mobi(&state.text, state.filename_display(), "Author", &path) {
                            Ok(()) => state.status_message = Some(format!(" Exported to {:?}", path)),
                            Err(msg) => state.status_message = Some(format!("MOBI: {}", msg)),
                        }
                        state.export_modal = false;
                    }
                    KeyCode::Char('q') | KeyCode::Char('Q') | KeyCode::Esc => {
                        state.export_modal = false;
                    }
                    _ => {}
                }
            }
            continue;
        }

        if state.fixing {
            if let Event::Key(key) = event {
                if key.code == KeyCode::Esc {
                    state.fixing = false;
                }
            }
            continue;
        }

        if let Event::Key(key) = event {
            match (key.code, key.modifiers) {
                (KeyCode::Tab, _) => {
                    if !state.ollama_online {
                        state.status_message = Some(" Ollama offline".to_string());
                        continue;
                    }

                    let cursor_pos = state.text.len().min(state.text.len());
                    let (line_text, start_byte, end_byte) = get_current_line(&state.text, cursor_pos);

                    if line_text.trim().is_empty() {
                        state.status_message = Some(" Nothing to fix".to_string());
                        continue;
                    }

                    state.fixing = true;
                    state.status_message = None;
                    render_editor(&mut terminal, &state)?;

                    let (tx, mut rx) = mpsc::channel::<Result<String, String>>(1);
                    let line_clone = line_text.clone();
                    let model = config.model.clone();
                    let url = config.ollama_url.clone();

                    std::thread::spawn(move || {
                        let rt = tokio::runtime::Builder::new_current_thread()
                            .enable_all()
                            .build()
                            .unwrap();
                        let result = rt.block_on(ollama::call_ollama(&line_clone, &model, &url));
                        let _ = tx.blocking_send(result);
                    });

                    loop {
                        match rx.try_recv() {
                            Ok(Ok(response)) => {
                                let improved = response.trim().to_string();
                                state.text = replace_range(&state.text, start_byte, end_byte, &improved);
                                state.fixing = false;
                                state.dirty = true;
                                state.status_message = Some(" ✦ Fixed".to_string());
                                last_save = Instant::now();
                                break;
                            }
                            Ok(Err(e)) => {
                                state.fixing = false;
                                state.status_message = Some(format!(" Ollama error: {}", e));
                                break;
                            }
                            Err(mpsc::error::TryRecvError::Empty) => {
                                std::thread::sleep(Duration::from_millis(80));
                                continue;
                            }
                            Err(mpsc::error::TryRecvError::Disconnected) => {
                                state.fixing = false;
                                state.status_message = Some(" Fix failed".to_string());
                                break;
                            }
                        }
                    }
                }

                (KeyCode::Char('s'), KeyModifiers::CONTROL) => {
                    let path = state.save_path();
                    match std::fs::write(&path, &state.text) {
                        Ok(()) => {
                            state.dirty = false;
                            state.status_message = Some(format!(" Saved to {:?}", path));
                            last_save = Instant::now();
                        }
                        Err(e) => {
                            state.status_message = Some(format!(" Save failed: {}", e));
                        }
                    }
                }

                (KeyCode::Char('e'), KeyModifiers::CONTROL) => {
                    state.export_modal = true;
                    state.status_message = None;
                }

                (KeyCode::Char('g'), KeyModifiers::CONTROL) => {
                    state.word_count_visible = !state.word_count_visible;
                }

                (KeyCode::Char('q'), KeyModifiers::CONTROL) => {
                    if state.dirty {
                        let path = state.save_path();
                        if std::fs::write(&path, &state.text).is_err() {
                            state.status_message = Some(" Save failed".to_string());
                            continue;
                        }
                    }
                    let _ = std::fs::remove_file(state.autosave_path());
                    break 'main_loop;
                }

                (KeyCode::Esc, _) => {
                    state.status_message = None;
                }

                (KeyCode::Char(c), _) => {
                    state.text.push(c);
                    state.dirty = true;
                }

                (KeyCode::Enter, _) => {
                    state.text.push('\n');
                    state.dirty = true;
                }

                (KeyCode::Backspace, _) => {
                    if !state.text.is_empty() {
                        state.text.pop();
                        state.dirty = true;
                    }
                }

                _ => {}
            }
        }
    }

    let _ = execute!(std::io::stderr(), crossterm::terminal::LeaveAlternateScreen);
    let _ = execute!(std::io::stderr(), crossterm::event::DisableMouseCapture);

    Ok(())
}
