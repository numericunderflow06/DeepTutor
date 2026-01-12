# DeepTutor RAG System - How It Works

This document explains how the Retrieval-Augmented Generation (RAG) system works in DeepTutor, including the knowledge base processing pipeline and what the LLM model sees during chat.

## Overview

DeepTutor uses a hybrid RAG system that combines:
1. **Vector Search** - Semantic similarity matching
2. **Knowledge Graph** - Entity and relationship extraction
3. **Multimodal Processing** - Images, tables, and equations from PDFs

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│                    (http://localhost:3782)                          │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         CHAT AGENT                                   │
│  - Receives user message                                            │
│  - Checks if RAG is enabled                                         │
│  - Retrieves context from knowledge base                            │
│  - Builds prompt with context                                       │
│  - Sends to LLM                                                     │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
┌──────────────────────────┐    ┌──────────────────────────┐
│      RAG SERVICE         │    │      LLM PROVIDER        │
│  (Knowledge Base Search) │    │  (Claude Code CLI)       │
└──────────────────────────┘    └──────────────────────────┘
```

## Knowledge Base Creation Pipeline

When you upload a PDF to create a knowledge base, here's what happens:

### Step 1: Document Parsing (MinerU)
```
PDF File
    │
    ▼
┌─────────────────────────────────────────┐
│           MinerU Parser                  │
│  - Extracts text content                │
│  - Identifies images, tables, equations │
│  - Preserves document structure         │
│  - Creates content_list.json            │
└─────────────────────────────────────────┘
    │
    ▼
Content List (JSON with all extracted elements)
```

### Step 2: Text Chunking
```
Content List
    │
    ▼
┌─────────────────────────────────────────┐
│         Semantic Chunker                 │
│  - Splits text into meaningful chunks   │
│  - Preserves context boundaries         │
│  - Typical chunk size: 500-1000 tokens  │
└─────────────────────────────────────────┘
    │
    ▼
Text Chunks (stored in rag_storage/)
```

### Step 3: Embedding & Indexing
```
Text Chunks
    │
    ▼
┌─────────────────────────────────────────┐
│       Embedding Service (Ollama)         │
│  - Model: nomic-embed-text              │
│  - Converts text to 768-dim vectors     │
│  - Enables semantic similarity search   │
└─────────────────────────────────────────┘
    │
    ▼
Vector Index (for similarity search)
```

### Step 4: Knowledge Graph Construction (LightRAG)
```
Text Chunks
    │
    ▼
┌─────────────────────────────────────────┐
│      LightRAG Knowledge Graph            │
│  - Extracts entities (concepts, terms)  │
│  - Identifies relationships             │
│  - Builds graph structure               │
│  - Enables graph-based retrieval        │
└─────────────────────────────────────────┘
    │
    ▼
Knowledge Graph (graph_chunk_entity_relation.graphml)
```

## Knowledge Base Directory Structure

```
data/knowledge_bases/
└── Linear Algebra/
    ├── raw/                    # Original uploaded files
    │   └── script-la.pdf
    ├── content_list/           # Parsed content (JSON)
    │   └── script-la.json
    ├── images/                 # Extracted images
    ├── rag_storage/            # RAG index data
    │   ├── graph_chunk_entity_relation.graphml
    │   ├── kv_store_text_chunks.json
    │   ├── kv_store_full_entities.json
    │   ├── kv_store_full_relations.json
    │   └── vdb_chunks/         # Vector database
    ├── metadata.json           # KB metadata
    └── .progress.json          # Processing progress
```

## RAG Query Process (What Happens When You Chat)

### When RAG is DISABLED (rag=False)
```
User: "Explain eigenvalues"
         │
         ▼
┌─────────────────────────────────────────┐
│            Chat Agent                    │
│  Just sends message directly to LLM     │
│  NO knowledge base content retrieved    │
└─────────────────────────────────────────┘
         │
         ▼
LLM responds using ONLY its general knowledge
(May not match your specific document)
```

### When RAG is ENABLED (rag=True)
```
User: "Explain eigenvalues"
         │
         ▼
┌─────────────────────────────────────────┐
│          RAG Search Tool                 │
│  1. Embeds the query                    │
│  2. Searches vector index               │
│  3. Traverses knowledge graph           │
│  4. Retrieves relevant chunks           │
└─────────────────────────────────────────┘
         │
         ▼
Retrieved Context (from YOUR document):
"In linear algebra, eigenvalues are scalars
associated with a linear system of equations...
[Definition 3.2] An eigenvalue λ of matrix A..."
         │
         ▼
┌─────────────────────────────────────────┐
│            Chat Agent                    │
│  Combines context + user question       │
│  into a single prompt for the LLM       │
└─────────────────────────────────────────┘
         │
         ▼
```

## What the LLM Actually Sees

When RAG is enabled, the LLM receives a prompt like this:

```
[System Prompt]
You are a helpful tutor assistant...

[Knowledge Base: Linear Algebra]
Retrieved content from your document:

"Chapter 3: Eigenvalues and Eigenvectors

Definition 3.1: Let A be an n×n matrix. A scalar λ is called
an eigenvalue of A if there exists a nonzero vector v such that
Av = λv. The vector v is called an eigenvector corresponding to λ.

Theorem 3.2: The eigenvalues of a matrix A are the roots of the
characteristic polynomial det(A - λI) = 0.

Example 3.1: Find the eigenvalues of matrix A = [[2, 1], [1, 2]]
Solution: det(A - λI) = (2-λ)² - 1 = λ² - 4λ + 3 = (λ-1)(λ-3)
Therefore, λ₁ = 1 and λ₂ = 3..."

[User Message]
Explain eigenvalues
```

The LLM then generates a response **grounded in your specific document content**.

## Search Modes

DeepTutor supports multiple search modes:

| Mode | Description | Best For |
|------|-------------|----------|
| `hybrid` | Combines vector + graph search | General queries (default) |
| `local` | Graph-based local context | Specific concept lookups |
| `global` | Graph-based global themes | High-level summaries |
| `naive` | Simple vector similarity | Quick keyword matching |

## Key Components

### 1. RAGAnything Pipeline
- Wraps MinerU (PDF parsing) + LightRAG (knowledge graph)
- Handles multimodal content (images, tables, equations)
- Best for academic/technical documents

### 2. Embedding Service (Ollama)
- Model: `nomic-embed-text`
- Dimensions: 768
- Runs locally, no API key needed

### 3. LLM Provider (Claude Code CLI)
- Uses your Max subscription
- Model: `claude-opus-4-5-20251101`
- Provides intelligent responses grounded in retrieved content

## Enabling RAG in the UI

1. Click the **"RAG" button** in the chat interface (must be highlighted/ON)
2. Select your **knowledge base** from the dropdown
3. Type your question and send

When RAG is active, you'll see:
- "Searching knowledge base..." during retrieval
- Sources cited in the response

## Troubleshooting

### RAG not finding content?
- Ensure the knowledge base processing completed (check for files in `rag_storage/`)
- Try rephrasing your query
- Check if RAG toggle is ON in the UI

### Processing failed?
- Enable Windows Developer Mode for MinerU symlink support
- Check logs for specific errors
- Ensure Ollama is running for embeddings

## File References

- RAG Service: `src/services/rag/service.py`
- RAG Tool: `src/tools/rag_tool.py`
- Chat Agent: `src/agents/chat/chat_agent.py`
- Knowledge Initializer: `src/knowledge/initializer.py`
- RAGAnything Pipeline: `src/services/rag/pipelines/raganything.py`
