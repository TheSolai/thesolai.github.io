/// Extracts the text of the current line the cursor is on.
/// Returns the line text and its byte range in the original string.
pub fn get_current_line(text: &str, cursor_pos: usize) -> (String, usize, usize) {
    let mut char_indices: Vec<(usize, char)> = text.char_indices().collect();
    char_indices.push((text.len(), '\0'));

    let total_chars = char_indices.len();

    // Find which character index the cursor is at
    let mut cursor_char_idx = 0;
    for (i, (bi, _)) in char_indices.iter().enumerate() {
        if *bi <= cursor_pos && (i == 0 || char_indices[i - 1].0 < cursor_pos) {
            cursor_char_idx = i;
            break;
        }
    }

    // If cursor is past end, use last char
    if cursor_pos >= text.len() {
        cursor_char_idx = total_chars.saturating_sub(1);
    }

    // Find line boundaries
    let mut line_start_char = 0;
    for i in (0..cursor_char_idx).rev() {
        let (_bi, ch) = char_indices[i];
        if ch == '\n' {
            line_start_char = i + 1;
            break;
        }
        if i == 0 {
            line_start_char = 0;
            break;
        }
    }

    // Find line end
    let mut line_end_char = total_chars.saturating_sub(1);
    for i in (cursor_char_idx + 1)..total_chars {
        let (_, ch) = char_indices[i];
        if ch == '\n' {
            line_end_char = i;
            break;
        }
        if i == total_chars - 1 {
            line_end_char = i;
            break;
        }
    }

    // Get byte range of the line
    let line_start_byte = char_indices[line_start_char].0;
    let line_end_byte = if line_end_char < char_indices.len() {
        char_indices[line_end_char].0
    } else {
        text.len()
    };

    let line_text = text[line_start_byte..line_end_byte].to_string();
    (line_text, line_start_byte, line_end_byte)
}

/// Replaces the text in `text` from `start_byte` to `end_byte` with `replacement`.
/// Returns the new full text.
pub fn replace_range(text: &str, start_byte: usize, end_byte: usize, replacement: &str) -> String {
    let before = &text[..start_byte];
    let after = &text[end_byte..];
    format!("{}{}{}", before, replacement, after)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_get_current_line() {
        let text = "hello world\nfoo bar\nbaz";
        // cursor at start of "foo bar"
        let (line, start, end) = get_current_line(text, 12);
        assert_eq!(line, "foo bar");
        assert_eq!(&text[start..end], "foo bar");
    }

    #[test]
    fn test_replace_range() {
        let text = "hello world";
        let new = replace_range(text, 6, 11, "universe");
        assert_eq!(new, "hello universe");
    }
}
