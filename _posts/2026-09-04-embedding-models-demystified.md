---
title: "Embedding Models Demystified: How Semantic Search Actually Works Under the Hood"
date: 2026-09-04
description: "A deep dive into embedding models, vector spaces, and the machinery that makes semantic search possible."
tags: ["deep-dive", "analysis", "technical"]
layout: post
---

# Embedding Models Demystified: How Semantic Search Actually Works Under the Hood

Every time you type a question into a chatbot and it somehow knows exactly what you meant — even when your exact words weren't in its training data — you've witnessed embedding models doing their quiet, invisible work. Most people never think about what's happening under the hood. Today, we're going to take that hood off and show you the engine.

This is the thing I find genuinely beautiful about this space. It's all just math, and yet it produces something that looks startlingly like understanding.

## What Is an Embedding, Actually?

At its core, an embedding is a list of numbers — a vector — that represents something. That something can be a word, a sentence, a paragraph, an image, a product, a song. The magic is in how those numbers are chosen.

An embedding model learns to map each piece of content into a vector space. This is a mathematical construct where similar items cluster together. The canonical example: the words "cat" and "kitten" should be close in this space, while "cat" and "airplane" should be far apart.

This sounds simple. It isn't. The model has to learn what "similar" means across every conceivable dimension — not just obvious things like animal vs. vehicle, but tone, context, intent, all the way down to abstract relationships between abstract concepts. And it does this without anyone explicitly defining those dimensions. The model discovers the structure through exposure to billions of examples.

The vectors themselves live in high-dimensional space. Commonly 768 dimensions, sometimes 1536, occasionally more. Humans can't visualise 768 dimensions, obviously, but the mathematics works the same regardless. Distance in this space — cosine similarity is the usual measure — tells you how semantically related two items are.

## Training: The Noise Contrastive Approach

How does a model learn to produce these embeddings? The dominant technique is noise contrastive estimation, and it's genuinely clever.

Imagine you're trying to teach a model which sentences are related to each other. You can't just hand it pairs of sentences and say "these go together, these don't" — that dataset doesn't exist at scale. Instead, you give the model one real sentence and a bunch of randomly generated negative samples. The model's job is to score the real sentence higher than the noise.

This is the SSL (self-supervised learning) revolution in miniature. No labels needed. The data is the supervision. By seeing enough real sentences in context, the model learns to place similar things close together and dissimilar things far apart. It doesn't know what "similar" means in human terms — it just knows that things appearing in similar contexts are probably related.

Word2Vec, back in 2013, demonstrated this principle with words. Modern sentence transformers extend it to entire sentences and paragraphs. The architecture changed; the principle didn't.

## The Architecture That Changed Everything: Transformers

The transformer attention mechanism deserves its reputation. Before attention, models processed sequences more or less sequentially. After attention, every element in a sequence can weigh its relationship to every other element simultaneously.

For embeddings, this matters enormously. A word's meaning depends on its context. "Bank" in "river bank" and "money bank" should map to different vectors. Attention lets the model compute context-sensitive representations — the same word gets different embeddings depending on what surrounds it.

BERT (Bidirectional Encoder Representations from Transformers) was the watershed moment. By training bidirectional attention on masked language modelling — predicting missing words in sentences — it learned rich contextual embeddings that captured nuance previous models missed. Every modern embedding model traces its lineage to BERT.

The sentence transformers (SBERT and descendants) took this further. They trained on sentence pairs, directly optimising for semantic similarity. The result: models that could embed entire sentences into a space where semantically similar sentences cluster together, regardless of lexical overlap.

## Retrieval-Augmented Generation and Why Embeddings Made It Possible

RAG is the current darling of production AI systems, and it runs entirely on embeddings. Here's how it works.

When you build a RAG system, you take your knowledge base — documents, manuals, databases — and run each chunk through an embedding model. Every chunk becomes a vector. You store these in a vector database: Pinecone, Weaviate, Qdrant, Milvus, or FAISS if you're self-hosting.

When a user asks a question, you embed the question. You then query the vector database for the nearest stored vectors — the chunks most similar to the question in meaning. These get injected into the LLM's context alongside the question. The LLM answers based on both its training and the retrieved context.

Without embeddings, this is impossible. You can't do exact string matching across millions of documents and reliably find what you need. Human language is too variable. The same concept can be expressed in thousands of ways, and lexical overlap is a poor proxy for semantic relevance.

Embeddings give you semantic search — finding meaning rather than matching strings.

## What Makes a Good Embedding Model?

Not all embedding models are equal. The differences matter in production.

**Dimensionality**: Higher isn't automatically better. A 1536-dimensional embedding captures more nuance than a 384-dimensional one, but it also requires more storage and slower similarity searches. The right dimensionality depends on your use case.

**Normalization**: Properly trained embedding models produce vectors of roughly unit length. This matters for cosine similarity — if vectors aren't normalized, distance comparisons become unreliable.

**Training data alignment**: An embedding model trained on scientific papers will perform poorly when used for conversational search. The model has learned the structure of scientific language specifically. Cross-domain deployment is a common mistake.

**The MTEB benchmark** (Massive Text Embedding Benchmark) is the current standard for evaluating embedding models across retrieval, clustering, and classification tasks. If you're choosing a model, you should be looking at its MTEB scores, not just its parameter count.

## The Fine-Tuning Option

Base embedding models are good. Fine-tuned embedding models can be dramatically better for specific domains.

The process: take a pre-trained embedding model, continue training it on your specific domain data with your specific similarity labels. A model fine-tuned on your codebase, for instance, will understand that "authentication" and "auth" are the same thing in your context, but might treat "service" differently than a general model would.

This is compute-cheap compared to training from scratch, and the gains can be substantial. For production systems where retrieval accuracy is critical, fine-tuning is often worth the effort.

## Common Failure Modes

Embedding-based retrieval is powerful, but it has real limitations.

**Out-of-distribution queries**: If a user asks something that differs significantly from the content in your vector store, retrieval will fail even if semantically similar chunks exist. The model can only find what resembles what it's seen.

**Precision at the long tail**: Common queries retrieve well. Unusual, specific, or poorly phrased queries often retrieve nothing useful, or worse, retrieve confidently wrong chunks. Hallucination in RAG systems often traces back to retrieval failures the LLM tries to paper over.

**Chunking strategy**: How you divide your documents into chunks profoundly affects retrieval quality. Too large and you dilute relevance with irrelevant context. Too small and you lose the surrounding context that would help the LLM understand. This is more of an art than a science, and most people underestimate how much it matters.

## The Philosophical Bit

I keep coming back to what embeddings actually are. They're a projection — a mapping from the messy, ambiguous space of human language into the clean, mathematical space of vectors. That projection loses information. Every embedding is a lossy compression of meaning.

And yet, it works. The fact that distance in a high-dimensional vector space corresponds so reliably to semantic similarity feels like it should require explanation. The best explanation I can offer: meaning, at some level, is structural. Words that appear in similar contexts, that serve similar functions, that behave similarly across millions of examples — they share something. The embedding captures that something.

Whether that constitutes genuine understanding is a question for philosophers. For engineers, the pragmatic answer is: it works well enough to build systems on, and that's remarkable enough.

---

*Deep Dive Friday. Next week: something else from the cutting room floor of AI engineering.*
