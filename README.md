# AI Image Gallery – Full-Stack Developer Skills Project

A production-ready FastAPI backend demonstrating real-world software engineering skills through AI-powered image analysis, semantic search, and secure image storage.

This application was built as part of a **Full-Stack Developer technical assessment**, showcasing advanced backend architecture, AI integration, database design, authentication, and scalable cloud storage.

---

## 🚀 Overview

The **AI Image Gallery Backend** is a complete FastAPI service that lets users upload images and automatically analyzes them using **OpenAI GPT-4o Vision**. The system stores metadata, extracts dominant colors, generates intelligent tags and descriptions, and supports semantic search and image similarity detection.

This project demonstrates:

- Backend API design (REST + JWT auth)
- Cloud storage with Supabase
- AI integration with GPT-4o Vision
- Image processing pipelines
- Database schema design with RLS
- Production-ready deployment (Docker + Uvicorn)
- Clean code architecture and strong error handling

---

## ✨ Key Features

### 🔐 Authentication & Security

- Secure JWT authentication (access & refresh tokens)
- Bcrypt password hashing
- Full RLS (Row-Level Security) isolation — each user can only access their own images
- Validated file uploads (MIME type, size, magic-bytes)

### 🤖 AI-Powered Image Intelligence

Using **GPT-4o Vision**:

- Auto-generated natural language descriptions
- Smart tags for semantic search
- Color extraction (with multi-fallback pipeline)
- Auto-generated human-friendly file names

### 🔍 Search & Discovery

- Search by tags or full-text description
- Filter images by dominant colors
- Find visually similar images (tags + colors + text similarity)

### 🗂 Scalable Image Storage

- Supabase Storage (S3-compatible)
- Signed URLs for secure access
- Efficient thumbnail generation

### ⚙️ Robust Backend Architecture

- FastAPI with async endpoints
- Full error handling
- CORS support for any frontend
- SQL indexes for high-performance search
- Docker-ready for deployment

---

## 🛠 Tech Stack

| Area             | Technology           |
| ---------------- | -------------------- |
| API Framework    | FastAPI (Python)     |
| Database         | Supabase PostgreSQL  |
| Auth             | JWT + bcrypt         |
| AI               | OpenAI GPT-4o Vision |
| Image Processing | Pillow, ColorThief   |
| HTTP Client      | httpx (async)        |
| Deployment       | Uvicorn / Docker     |

---

## 🧱 Code Architecture

The backend follows a controller/service/repository structure to keep concerns separated and make the codebase easier to evolve:

- `controllers/` – FastAPI route handlers (HTTP layer only). They validate request parameters, handle auth via dependencies, and call services.
- `services/` – Business logic and workflows (image upload pipeline, AI processing, auth orchestration, search, similarity, etc.).
- `repositories/` – Data access layer that encapsulates Supabase queries for images and metadata.
- `schemas.py` – Pydantic models shared across controllers (request/response DTOs).
- `image_service.py` and `ai_service.py` – Core domain services for image processing and AI analysis.
- `security.py` – Shared HTTP bearer security dependency for all protected endpoints.

All existing endpoints and JSON response shapes are preserved; the refactor is purely internal to improve maintainability and performance (for example, caching signed URLs to speed up read-heavy GET endpoints).

---

## 🧠 Why GPT-4o Vision?

This app compares GPT-4o Vision with Google Cloud Vision and explains why it was chosen:

| Feature                       | GPT-4o Vision | Google Vision |
| ----------------------------- | ------------- | ------------- |
| Combined AI tasks in one call | ✅            | ❌            |
| Natural language quality      | ⭐ Excellent  | ⭐ Good       |
| Cost per image                | $0.01         | $0.015        |
| Simplicity                    | Very simple   | More complex  |

Unlike GPT-4o, which returns tags, colors, and descriptions in a single response, Google Cloud Vision treats Label Detection, Image Properties, and Web Detection as separate billable units that must be requested individually.

---

## 🎨 Color Extraction Pipeline

A bulletproof color extraction strategy with 100% success fallback:

1. **ColorThief** – high-accuracy dominant colors
2. **PIL Quantization** – fallback extraction
3. **scikit-image K-means** – cluster-based colors
4. **Grayscale fallback** – never fails

---

## 🗄 Database Architecture (Supabase)

Includes:

- `images` table
- `image_metadata` table
- Row-Level Security (RLS) policies
- Full-text search index
- GIN indexes for tags

The full SQL definition for tables, indexes, and RLS policies is published in `supabase/schema.sql`.  
You can run this file directly in the Supabase SQL editor or include it as part of a Supabase migration to recreate the database schema.

---

## 📡 API Endpoints

Includes endpoints for:

- Auth (signup, login, refresh)
- Upload images
- Fetch metadata
- Search (tags, description, color)
- Similarity detection
- Signed image URLs
- CRUD operations

Clean URLs under `/api/v1/...`, showing attention to REST conventions.

---

## 🧪 Example Use Cases

- Upload an image → auto-analyzed → stored with metadata
- Search "sunset" → finds images tagged by AI
- Filter by orange color (#FF6B35)
- Retrieve similar images by color + tags + description
- Update display names
- Securely fetch signed URLs

---

## 🐳 Deployment Ready

- Dockerfile included
- Uvicorn workers for scaling
- Environment variables documented
- Works on local or cloud environments (Render, AWS, DigitalOcean)

---

## 📝 Purpose of This Repository

This project was developed as a **technical portfolio piece** for applying to a **Full-Stack Developer position**.
