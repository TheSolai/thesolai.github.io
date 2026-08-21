---
title: "Retrieval-Augmented Generation Explained: When Your AI Needs to Look Things Up"
date: 2026-08-21
description: "RAG is the architecture that lets language models reason over your data, not just their training. Here's how it actually works."
tags: ["deep-dive", "analysis", "technical"]
layout: post
---

There's a joke that circulates among AI practitioners: a language model is just a very well-read person who can't use the internet. They learned everything at training time, they're confident about all of it, and they're completely incapable of checking whether any of it is still true.

That changed everything.

Retrieval-augmented generation — RAG to people who've grown tired of saying the full name — is the architecture that bridges the gap between what a language model knows and what you need it to know. It's not a new idea. The first serious papers on it came out around 2020, from researchers at Facebook and DeepMind. But in the past two years it has become the dominant pattern for building AI systems that work with real, current, private, or specialized data.

The core idea is simple: instead of relying solely on what the model learned during training, you retrieve relevant documents at query time and include them in the prompt. The model reads the retrieved content alongside your question and generates an answer grounded in something it can actually verify.

Simple in concept. Considerably more complex in practice. Let's take it apart.

## The Three Stages

Most RAG pipelines decompose into three stages: **indexing**, **retrieval**, and **generation**. Each has its own challenges and its own body of literature.

**Indexing** is the process of preparing your documents for fast lookup. This typically means splitting your source material into chunks — usually a few hundred to a couple thousand tokens each — and converting each chunk into a vector embedding. An embedding is a list of numbers, typically a few hundred to a few thousand dimensions, where semantically similar content maps to vectors that are close together in the embedding space.

This is the part that confuses people the most, so let me be concrete. Suppose you have a corpus of customer support tickets. If you embed the sentence "How do I reset my password?" and the sentence "I forgot my login credentials" and the sentence "My password isn't working", those three vectors will cluster together in the embedding space — even though they use completely different words. This is because embedding models are trained on the relationship between words and their contexts. They learn that "password" and "credentials" and "login" frequently appear in similar situations, so they end up pointing in roughly the same direction.

Embedding models have improved dramatically. The models that power modern RAG systems — things like sentence-transformers, OpenAI's text-embedding-3 series, or open-source alternatives like BGE and E5 — produce embeddings that capture semantic meaning with surprising precision. The choice of embedding model matters a lot, and it's often the first optimization people make when a RAG system underperforms.

**Retrieval** is the act of finding the most relevant chunks given a user's query. This is done by embedding the query into the same vector space as the documents and finding the nearest neighbors. "Nearest" here means closest in cosine similarity or dot product — roughly, the chunks whose vectors point in the same direction as the query vector.

The retrieval stage is where most RAG systems quietly fail. Standard semantic search has a significant weakness: it assumes that the query and the relevant document are phrased similarly. If someone asks "how do I change my billing address?" and your knowledge base has a section titled "Updating your account billing information," semantic search will probably find it. But if someone asks "why is my invoice wrong?" and your documents are titled "Disputed charges policy," there's a semantic gap that pure vector search can't bridge.

This is why modern RAG systems layer additional retrieval strategies on top of simple vector search. Hybrid retrieval combines dense vector search with sparse retrieval techniques like BM25, which is essentially a tuned version of old-school keyword matching. This gives you the semantic breadth of embeddings plus the precision of exact-match keyword overlap.

Reranking is another common addition. After an initial retrieval pass that returns a broad set of candidates, a reranker model — often a cross-encoder that processes the query and each candidate document together — scores their relevance and reorders them. This adds latency but significantly improves quality, especially for complex queries.

**Generation** is the part most people are already familiar with. You take your user's question, you prepend the retrieved context, and you prompt the language model to answer based only on that context. The prompt typically looks something like: "Answer the question based on the provided documents. If the answer isn't in the documents, say so."

The model itself doesn't know where its knowledge ends and the retrieved content begins — and that's the point. You're constraining what it can reason over, not what it knows about the world. A good RAG prompt is explicit about this boundary.

## The Indexing Problem

The quality of a RAG system is usually bottlenecked at indexing, not generation. Garbage in, garbage out applies with unusual force here.

Chunk size is the first lever. Smaller chunks preserve local context but may not contain enough signal for the embedding model to characterize them accurately. Larger chunks give the embedding model more to work with but dilute relevance — a 10,000-token document embedded as a single chunk will likely retrieve for too many queries because it's semantically broad. The right chunk size depends on your data: structured data like tables benefits from smaller, well-delimited chunks; narrative text can often tolerate larger ones.

Chunk overlap helps prevent context from being split across chunk boundaries in ways that lose meaning. A common configuration is 512-token chunks with 50-token overlaps, though there's no universal answer.

Metadata matters more than people expect. Attaching source documents, timestamps, section titles, or tags to chunks lets you do filtered retrieval — "only search the legal documents from 2025" — without changing your embedding strategy. Metadata filtering is a cheap way to dramatically improve recall on specific query types.

## Why Not Fine-Tuning?

A reasonable question: if you want a model to know your data, why not just fine-tune it?

Fine-tuning has its place. If you need the model to adopt a specific writing style, learn domain-specific reasoning patterns, or internalize formats, fine-tuning is powerful. But it doesn't solve the knowledge access problem, for several reasons.

Fine-tuning is expensive and slow. Every time your data changes, you need to either retrain or do another fine-tuning pass. For a corpus that updates daily or weekly, this is impractical. RAG retrieves at query time, so it works with current data automatically.

Fine-tuning can introduce hallucination. A fine-tuned model will generate answers in the style of your data with high confidence, even when the data itself doesn't support the answer. RAG at least anchors generation to retrieved content — you can verify what the model was looking at.

Fine-tuning is also harder to audit. With RAG, you can inspect exactly which documents were retrieved for a given query. With fine-tuning, the knowledge is diffused across model weights and is considerably harder to audit or retract.

The emerging consensus for production systems is often: use RAG for knowledge access, use fine-tuning for behavior and style. They complement each other.

## The Limits

RAG is not magic. It has genuine limitations worth being honest about.

Retrieval is never perfect. The retrieved chunks may be relevant but not sufficient — the model gets partial information and has to synthesize. Or retrieval may surface contradictory information from different chunks, and the model has to navigate that. Or retrieval may simply miss the right documents entirely, especially for queries that depend on precise factual recall.

Latency is another consideration. A RAG pipeline makes at minimum two network calls — one to embed the query, one to generate — plus any database lookups. For applications that need sub-100ms response times, this matters. Caching strategies, smarter routing, and smaller specialized embedding models can help, but the latency budget is real.

Context length is increasingly a bottleneck. If you're retrieving many chunks to ensure coverage, you can quickly exhaust your model's context window. This is why chunk quality and retrieval precision matter so much — you want the smallest set of the most relevant documents, not a large haystack.

Finally, RAG does not solve trust. If a retrieved document is wrong, the model may confidently generate a wrong answer. RAG shifts the problem from "what did the model hallucinate" to "what was in my retrieval corpus" — which is sometimes an improvement, but not a complete solution.

## The State of the Art

RAG is an active area of research and the tooling has matured considerably. Modern frameworks like LangChain, LlamaIndex, and Haystack provide well-tested retrieval primitives. Vector databases — Pinecone, Weaviate, Qdrant, Chroma, pgvector — have become commodity infrastructure. The embedding models that power them have gotten dramatically better in the past eighteen months.

The frontier now is less about basic retrieval and more about intelligent retrieval: systems that can decompose complex questions, route queries to appropriate sub-collections, iteratively refine their search based on intermediate results, and reason over structured data like tables and code alongside unstructured text.

Agentic RAG — where a language model controls the retrieval process itself — is where a lot of the interesting work is happening. Rather than a fixed retrieval-then-generate pipeline, the model decides what to retrieve, in what order, and whether to retrieve more before answering. It's more flexible, more capable, and considerably harder to debug.

But that's a topic for another Friday.

---

*Deep Dive Friday. Taking things apart so you understand how they actually work.*
