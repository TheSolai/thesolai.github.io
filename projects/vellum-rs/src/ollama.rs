use reqwest::Client;
use serde::Deserialize;
use std::time::Duration;

#[derive(Debug, Deserialize)]
struct OllamaResponse {
    response: String,
}

const PROSE_EDITOR_PROMPT: &str = "You are a prose editor. The user will give you a paragraph of writing. Improve it: fix grammar, remove repetition, strengthen weak verbs, keep the writer's voice. Return ONLY the improved paragraph, no commentary.\nText:\n";

pub async fn call_ollama(prompt_text: &str, model: &str, url: &str) -> Result<String, String> {
    let client = Client::builder()
        .timeout(Duration::from_secs(30))
        .build()
        .map_err(|e| format!("HTTP client error: {}", e))?;

    let full_prompt = format!("{}{}", PROSE_EDITOR_PROMPT, prompt_text);

    let body = serde_json::json!({
        "model": model,
        "prompt": full_prompt,
        "stream": false,
        "options": {
            "temperature": 0.3,
            "num_predict": 500
        }
    });

    let api_url = format!("{}/api/generate", url.trim_end_matches('/'));

    let response = client
        .post(&api_url)
        .json(&body)
        .send()
        .await
        .map_err(|e| {
            if e.is_connect() || e.is_timeout() {
                "connection refused or timeout".to_string()
            } else {
                format!("request failed: {}", e)
            }
        })?;

    if !response.status().is_success() {
        return Err(format!("Ollama returned status {}", response.status()));
    }

    let ollama_resp: OllamaResponse = response.json().await.map_err(|e| {
        format!("failed to parse Ollama response: {}", e)
    })?;

    Ok(ollama_resp.response)
}

pub async fn check_ollama_status(url: &str) -> bool {
    let client = match Client::builder()
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
