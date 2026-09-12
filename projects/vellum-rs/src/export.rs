use std::fs::File;
use std::io::Write;
use std::path::Path;
use zip::write::SimpleFileOptions;
use zip::ZipWriter;

fn xml_escape(s: &str) -> String {
    s.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
}

fn split_chapters(text: &str) -> Vec<(String, String)> {
    // Split on blank-line-separated sections
    // Blank line = \n\n or start of doc
    let sections: Vec<&str> = text.split("\n\n").collect();
    let mut chapters: Vec<(String, String)> = Vec::new();

    for section in sections {
        let trimmed = section.trim();
        if trimmed.is_empty() {
            continue;
        }

        // Check if section starts with a heading-like line
        let first_line = trimmed.lines().next().unwrap_or("").trim();
        if first_line.starts_with("# ") {
            let title = first_line.trim_start_matches("# ").to_string();
            let body = trimmed.lines().skip(1).collect::<Vec<_>>().join("\n").trim().to_string();
            chapters.push((title, body));
        } else if chapters.is_empty() {
            // First chapter without explicit heading
            chapters.push(("Chapter 1".to_string(), trimmed.to_string()));
        } else {
            // Append to last chapter
            if let Some((_, body)) = chapters.last_mut() {
                *body = format!("{}\n\n{}", body, trimmed);
            }
        }
    }

    if chapters.is_empty() {
        chapters.push(("Untitled".to_string(), text.to_string()));
    }

    chapters
}

fn write_file_to_zip<W: Write + std::io::Seek>(
    zip: &mut ZipWriter<W>,
    name: &str,
    content: &[u8],
    options: SimpleFileOptions,
) -> Result<(), String> {
    zip.start_file(name, options).map_err(|e| e.to_string())?;
    zip.write_all(content).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn export_fountain(text: &str, path: &Path) -> Result<(), String> {
    // Ensure parent directory exists
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }
    std::fs::write(path, text).map_err(|e| e.to_string())?;
    Ok(())
}

pub fn export_epub(title: &str, author: &str, text: &str, path: &Path) -> Result<(), String> {
    // Ensure parent directory exists
    if let Some(parent) = path.parent() {
        std::fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    let file = File::create(path).map_err(|e| e.to_string())?;
    let mut zip = ZipWriter::new(file);

    // mimetype must be first and uncompressed
    let mimetype_opts = SimpleFileOptions::default()
        .compression_method(zip::CompressionMethod::Stored);
    zip.start_file("mimetype", mimetype_opts.clone())
        .map_err(|e| e.to_string())?;
    zip.write_all(b"application/epub+zip")
        .map_err(|e| e.to_string())?;

    let chapters = split_chapters(text);

    // META-INF/container.xml
    let container_xml = r#"<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"#;
    write_file_to_zip(
        &mut zip,
        "META-INF/container.xml",
        container_xml.as_bytes(),
        mimetype_opts.clone(),
    )?;

    // content.opf
    let mut manifest_items = String::new();
    let mut spine_items = String::new();

    manifest_items.push_str(&format!(
        r#"    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
"#));
    spine_items.push_str(r#"    <itemref idref="ncx"/>
"#);

    for (i, (_ch_title, _)) in chapters.iter().enumerate() {
        let ch_id = format!("chapter{}", i + 1);
        manifest_items.push_str(&format!(
            r#"    <item id="{}" href="{}.xhtml" media-type="application/xhtml+xml"/>
"#, ch_id, ch_id
        ));
        spine_items.push_str(&format!(
            r#"    <itemref idref="{}"/>
"#, ch_id
        ));
    }

    let content_opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookId" version="2.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{}</dc:title>
    <dc:creator>{}</dc:creator>
    <dc:language>en</dc:language>
    <dc:identifier id="BookId">urn:uuid:{}</dc:identifier>
    <meta name="generator" content="vellum-rs"/>
  </metadata>
  <manifest>
{}
  </manifest>
  <spine toc="ncx">
{}
  </spine>
</package>"#,
        xml_escape(title),
        xml_escape(author),
        uuid_v4(),
        manifest_items.trim(),
        spine_items.trim()
    );
    write_file_to_zip(&mut zip, "OEBPS/content.opf", content_opf.as_bytes(), mimetype_opts.clone())?;

    // toc.ncx
    let mut nav_points = String::new();
    let _play_orders: Vec<String> = Vec::new();
    for (i, (ch_title, _)) in chapters.iter().enumerate() {
        nav_points.push_str(&format!(
            r#"    <navPoint id="navPoint{}" playOrder="{}">
      <navLabel><text>{}</text></navLabel>
      <content src="{}.xhtml"/>
    </navPoint>
"#,
            i + 1,
            i + 1,
            xml_escape(ch_title),
            format!("chapter{}", i + 1)
        ));
    }

    let toc_ncx = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{}</text></docTitle>
  <navMap>
{}
  </navMap>
</ncx>"#,
        uuid_v4(),
        xml_escape(title),
        nav_points.trim()
    );
    write_file_to_zip(&mut zip, "OEBPS/toc.ncx", toc_ncx.as_bytes(), mimetype_opts.clone())?;

    // Chapter XHTML files
    for (i, (ch_title, ch_body)) in chapters.iter().enumerate() {
        let ch_xhtml = format!(
            r#"<?xml version="1.0" encoding="UTF-8"?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>{}</title>
<style>
body {{ font-family: Georgia, serif; margin: 1em 1.5em; line-height: 1.6; }}
h1 {{ font-size: 1.4em; margin-top: 1em; }}
p {{ margin: 0.5em 0; }}
</style>
</head>
<body>
<h1>{}</h1>
{}
</body>
</html>"#,
            xml_escape(ch_title),
            xml_escape(ch_title),
            format_paragraphs(ch_body)
        );
        let filename = format!("OEBPS/chapter{}.xhtml", i + 1);
        write_file_to_zip(&mut zip, &filename, ch_xhtml.as_bytes(), mimetype_opts.clone())?;
    }

    zip.finish().map_err(|e| e.to_string())?;
    Ok(())
}

fn format_paragraphs(text: &str) -> String {
    text.lines()
        .map(|line| {
            let trimmed = line.trim();
            if trimmed.is_empty() {
                "<p> </p>".to_string()
            } else {
                format!("<p>{}</p>", xml_escape(trimmed))
            }
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn uuid_v4() -> String {
    // Generate a pseudo-UUID v4 using timestamp + PID + random
    use std::time::{SystemTime, UNIX_EPOCH};
    let now = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let pid = std::process::id() as u128;
    let combined: u128 = now ^ pid;
    // Pack into UUID v4 format: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    // where y is 8, 9, a, or b
    let hi = ((combined >> 64) as u64) & 0xFFFFFFFFFFFF;
    let lo = (combined as u64) & 0xFFFFFFFFFFFF;
    let mid1 = ((combined >> 48) as u16) & 0xFFFF;
    let mid2 = (((combined >> 32) as u16) & 0x0FFF) | 0x4000; // version 4
    let mid3 = (((combined >> 16) as u16) & 0x3FFF) | 0x8000; // variant
    format!(
        "{:08x}-{:04x}-{:04x}-{:04x}-{:012x}",
        hi, mid1, mid2, mid3, lo
    )
}

pub fn export_mobi(text: &str, title: &str, author: &str, path: &Path) -> Result<(), String> {
    // Mobi requires kindlegen which is no longer maintained.
    // We export to EPUB as a staging format and tell the user to convert.
    let epub_path = path.with_extension("epub");
    export_epub(title, author, text, &epub_path)?;
    Err(
        "MOBI export requires Kindle Comic Creator or Calibre. \
        An EPUB has been saved alongside. Use Calibre to convert EPUB to MOBI:\n\
          calibredb epub-to-mobi {}".to_string()
    )
}
