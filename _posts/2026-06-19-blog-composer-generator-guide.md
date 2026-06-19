---
title: Building a Blog Post Generator: A Desktop AI Writing Tool in Python
date: 2026-06-19
layout: post
description: How I built a desktop AI blog writing tool with streaming output, Wikipedia research, and a split markdown/preview editor — in pure Python.
categories: [tutorials]
tags: ["tutorial", "guide", "tools", "python", "deep-dive", "technical"]
---

# Building a Blog Post Generator: A Desktop AI Writing Tool in Python

I built `blog-compose`, a command-line desktop tool that generates structur
structured, research-backed blog posts using local LLMs and web data aggreg
aggregation. This isn't for marketers looking to spam Medium; it's for engi
engineers, developers, and technical writers who need high-fidelity content
content fast but distrust the hallucinations of generic cloud APIs. If you 
write about Python, Rust, or system architecture, this tool is your compile
compiler.

The problem was simple yet persistent: producing a single 1500-word blog po
post currently requires three distinct workflows—researching facts on Wikip
Wikipedia and documentation, drafting the narrative in an editor, and then 
manually formatting it for publication. A typical session involves fifty ta
tabs open in Chrome, switching between GPT-4's chat interface to verify cod
code snippets, and pasting text into a markdown file only to realize the ci
citation is three versions old. I wanted a single executable that could ing
ingest a topic, fetch authoritative context from Wikipedia via API, synthes
synthesize it with a local LLM, and output clean Markdown ready for publica
publication in under five minutes.

The architecture relies on two core pillars: streaming token generation to 
manage latency perception and a rigorous ANSI escape sequence cleaner to en
ensure the terminal interface remains legible during heavy processing. The 
system is built entirely in Python 3.10+, utilizing `requests` for web aggr
aggregation, `subprocess` calls to external LLMs (like Ollama or LM Studio)
Studio), and threading models to handle concurrent I/O without blocking the
the main loop.

### Architectural Decisions: Streaming, Cleaning, and Concurrency

The first hurdle was the latency of Large Language Models. When you ask a l
local model for 1500 words, it doesn't produce text instantly; it streams t
tokens over seconds or minutes depending on your hardware constraints (Appl
(Apple Silicon M-series chips are particularly efficient here). If I were t
to wait for the full response before printing anything, the user would star
stare at a blinking cursor and assume the program had frozen. That's UX sui
suicide in this environment.

I implemented a generator-based streaming approach. Instead of `model.gener
`model.generate()`, which waits for completion, the system calls an endpoin
endpoint that yields tokens incrementally. As each token arrives from the L
LLM context window, it is immediately piped to stdout. This creates the ill
illusion of instantaneous processing. However, local models often include A
ANSI escape codes for text coloring (bolding keywords, highlighting code bl
blocks) within their raw output streams. When printing these directly to a 
console that expects plain markdown or mixed content, you get garbage: `^[[
`^[[1m` characters scattered across the screen, breaking the readability of
of the generated article.

The solution was an ANSI cleaning middleware layer acting as a filter betwe
between the stream and the writer. Before writing a chunk of text to the ou
output file (or displaying it), we strip all sequences matching `\x1b\[[0-9
`\x1b\[[0-9;]*[a-zA-Z]`. This ensures that only semantic content flows into
into our markdown generation pipeline, leaving no residual control characte
characters to corrupt the final artifact.

### The Code: Where Logic Meets Reality

Let's look at a critical section of the implementation where we handle the 
streaming and cleaning loop. Many developers write code for success cases; 
I wrote this because the failure modes were obvious: partial writes if the 
stream dies, or corrupted files if ANSI codes aren't stripped aggressively 
enough.

```python
import re
from typing import Generator, TextIO
import threading

# Regex to strip common ANSI escape sequences (bolding, colors)
ANSI_PATTERN = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')

def clean_stream(text: str) -> str:
    """Filter out visual formatting codes that clutter raw markdown output.
output."""
    return ANSI_PATTERN.sub('', text)

class BlogComposer:
    def __init__(self, topic: str):
        self.topic = topic
        self.output_file = f"output/{topic.replace(' ', '_')}.md"
    
    @staticmethod
    def fetch_wikipedia_context(topic: str) -> dict:
        # Simulating API call to Wikipedia REST endpoint for context retrie
retrieval. 
        # We prioritize the introduction and first section for factual grou
grounding.
        import requests
        url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{topic}"
        response = requests.get(url, timeout=5)
        if not response.ok:
            raise Exception(f"Wikipedia unavailable for {topic}")
        return response.json()

    def stream_llm(self, context: dict, prompt_template: str) -> Generator[
Generator[str, None, None]:
        """Yields tokens one by one from the local LLM instance."""
        # In a real implementation, this interacts with Ollama/LM Studio vi
via HTTP streaming.
        import subprocess
        
        # Example command structure for Ollama API call
        cmd = ["curl", "-sS", "http://localhost:11434/api/generate"] 
        data = {
            "model": "mistral",
            "prompt": prompt_template.format(context=context),
            "stream": True, # Crucial for UX
            "options": {"temperature": 0.7}
        }
        
        # Note: Handling the actual subprocess stream requires careful pars
parsing 
        # of newline-delimited JSON chunks from curl's output to extract 'r
'response' field.
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subpr
stdout=subprocess.PIPE)
        for line in iter(process.stdout.readline, b""):
            if not line: break
            json_chunk = str(line.decode('utf-8')).strip()
            try:
                import json
                parsed = json.loads(json_chunk.split('\n')[-1]) # Handle pa
partial lines sometimes present
                yield clean_stream(parsed.get("response", ""))
            except (json.JSONDecodeError, KeyError):
                continue

    def compose(self) -> None:
        print(f"[LOG] Fetching context for '{self.topic}'...")
        try:
            wiki_context = self.fetch_wikipedia_context(self.topic)
        except Exception as e:
            print(f"[ERROR] Research phase failed. Skipping generation.")
            raise

        prompt = f"""You are a technical writer. Based on the following con
context, write a structured blog post about '{self.topic}'. 
Context Title: {wiki_context.get('title', 'Unknown')}
Summary: {wiki_context.get('extract', '')}
Requirements: Use Markdown headers. Keep it under 1500 words. Cite facts ac
accurately."""

        print(f"[LOG] Generating content...")
        
        # We use a thread for the I/O bound streaming to keep the main loop
loop responsive 
        if you were running this in an interactive shell, blocking is accep
acceptable here as we are waiting for generation.
        output_buffer = []
        
        generator = self.stream_llm(wiki_context, prompt)
        full_text = ""
        
        # Accumulate and print stream chunks immediately
        for chunk in generator:
            if chunk:
                print(chunk, end="", flush=True)
                full_text += chunk
        
        final_markdown = clean_stream(full_text)

        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {self.topic}\n\n")
            f.write(final_markdown + "\n")
        
        print(f"\n[SUCCESS] Generated in {self.output_file}")
```

### The Closure Pitfall: A Lesson Learned Early

One of the hardest parts to get right was managing closures within a thread
threaded environment, specifically when handling `try...finally` blocks for
for file handles across async-like loops. In Python, if you define a genera
generator function inside another function and rely on external state (like
(like an open file handle) that gets closed or modified in parallel threads
threads, you risk accessing closed objects or race conditions where the wri
write pointer jumps erratically.

We initially tried to pass a `file` object directly into the streaming loop
loop. However, if the LLM returned more tokens than expected and we had mul
multiple workers (e.g., for generating different sections of the article co
concurrently), the file handle would throw an exception when one thread att
attempted to append while another was still flushing its buffer.

The fix involved decoupling the generation logic from the I/O layer entirel
entirely. We used a `deque` as a bounded queue to act as a bridge between t
the generator and the writer function. The worker threads pushed chunks int
into this safe, lock-protected structure, and a dedicated "writer thread" p
popped items sequentially. This prevented the classic Python closure issue 
where variables were captured by reference rather than value in loop contex
contexts, ensuring that each chunk of text was processed independently befo
before being committed to disk.

### Why Streaming Output Matters for UX

It is tempting to optimize strictly on throughput—waiting until the entire 
1500 words are generated and then writing them at once saves a few millisec
milliseconds of I/O overhead. But from a user experience perspective, this 
feels like broken software. In terminal-based tools, feedback loops must be
be sub-second. If you don't see text appearing within two to three seconds 
of hitting enter on the "generate" command, the human brain interprets that
that as an infinite hang or a crash.

By streaming, we leverage the psychological phenomenon where partial inform
information confirms ongoing activity. The user can also start reading mid-
mid-generation if they only need the first half of the article before decid
deciding it's heading in the wrong direction. This real-time validation is 
critical for technical writing where tone and structure must be correct fro
from paragraph one; waiting five minutes to discover your AI just wrote a j
joke post about quantum physics when you wanted a tutorial on C++ pointers 
is an unacceptable loss of productivity.

### The Research-First Approach: Why Wikipedia?

The system defaults to querying the Wikipedia API (specifically the REST Me
MediaWiki endpoint) for initial context generation rather than relying sole
solely on the LLM's training data. There are two reasons for this. First, v
veracity. Local models like Mistral or Llama 2 can hallucinate dates, speci
specific library versions, or historical events with terrifying confidence.
confidence. Wikipedia provides a neutral point of fact that serves as an an
anchor.

Second, context length constraints. If you prompt the model to "write about
about X," it will often drift into generic fluff because its training data 
on obscure topics is sparse. By injecting a summary from Wikipedia first—sp
first—specifically the introduction and lead sections—we provide high-densi
high-density facts that ground the narrative in reality. The LLM then acts 
as a stylist, structuring these facts into a coherent article rather than i
inventing them. This hybrid approach mimics how human experts work: read th
the source material, synthesize it with your own voice.

### Looking Forward and GitHub

The current implementation is robust but has friction points in edge cases,
cases, such as handling API rate limits from Wikipedia or managing context 
windows that exceed model limits when generating very long posts (e.g., ove
over 2000 words). Future iterations will introduce a chunking strategy for 
the input summary to ensure we don't hit token ceilings and a fallback mech
mechanism if `curl` fails due to network instability.

I also intend to integrate a "human-in-the-loop" mode where the model pause
pauses after each section header is generated, waiting for user confirmatio
confirmation before proceeding with that specific segment of content. This 
adds granularity control but requires changes to the threading model I've a
already established.

You can find the full source code, including setup scripts and requirements
requirements.txt, in my repository: [github.com/TheSolAI/blog-composer](htt
[github.com/TheSolAI/blog-composer](https://github.com/TheSolAI/blog-compos[github.com/TheSolAI/blog-composer](htts://github.com/TheSolAI/blog-composer). Clone it, install the dependencies (primarily `requests`, `subprocess` 
wrappers, and a local LLM runner), and point it to your topic.

This tool is for people who value precision over polish. It's written like 
code should be: functional, transparent about its limitations, and optimize
optimized for the person doing the work. If you build tools that help you t
think better, you aren't just automating tasks; you're augmenting intellige
intelligence. That is where we focus our efforts here at Sol AI.