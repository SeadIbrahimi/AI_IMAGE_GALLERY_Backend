# AI Image Gallery – Full-Stack Developer Skills Project

A production-ready FastAPI backend demonstrating real-world software engineering skills through AI-powered image analysis, semantic search, and secure image storage.

This application was built as part of a **Full-Stack Developer technical assessment**, showcasing advanced backend architecture, AI integration, database design, authentication, and scalable cloud storage.

---

## 🚀 Overview

The **AI Image Gallery Backend** is a complete FastAPI service that lets users upload images and automatically analyzes them using **OpenAI GPT-4o Vision**. The system stores metadata, extracts dominant colors, generates intelligent tags and descriptions, and supports semantic search and image similarity detection.

This project demonstrates:

* Backend API design (REST + JWT auth)
* Cloud storage with Supabase
* AI integration with GPT-4o Vision
* Image processing pipelines
* Database schema design with RLS
* Production-ready deployment (Docker + Uvicorn)
* Clean code architecture and strong error handling

---

## ✨ Key Features

### 🔐 Authentication & Security

* Secure JWT authentication (access & refresh tokens)
* Bcrypt password hashing
* Full RLS (Row-Level Security) isolation — each user can only access their own images
* Validated file uploads (MIME type, size, magic-bytes)

### 🤖 AI-Powered Image Intelligence

Using **GPT-4o Vision**:

* Auto-generated natural language descriptions
* Smart tags for semantic search
* Color extraction (with multi-fallback pipeline)
* Auto-generated human-friendly file names

### 🔍 Search & Discovery

* Search by tags or full-text description
* Filter images by dominant colors
* Find visually similar images (tags + colors + text similarity)

### 🗂 Scalable Image Storage

* Supabase Storage (S3-compatible)
* Signed URLs for secure access
* Efficient thumbnail generation

### ⚙️ Robust Backend Architecture

* FastAPI with async endpoints
* Full error handling
* CORS support for any frontend
* SQL indexes for high-performance search
* Docker-ready for deployment

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

## 🧠 Why GPT-4o Vision?

This app compares GPT-4o Vision with Google Cloud Vision and explains why it was chosen:

| Feature                       | GPT-4o Vision | Google Vision |
| ----------------------------- | ------------- | ------------- |
| Combined AI tasks in one call | ✅             | ❌             |
| Natural language quality      | ⭐ Excellent   | ⭐ Good        |
| Cost per image                | $0.01         | $0.015        |
| Simplicity                    | Very simple   | More complex  |

This demonstrates thoughtful **cost-performance analysis** — a valuable engineering skill.

---

## 🎨 Color Extraction Pipeline

A bulletproof color extraction strategy with 100% success fallback:

1. **ColorThief** – high-accuracy dominant colors
2. **PIL Quantization** – fallback extraction
3. **scikit-image K-means** – cluster-based colors
4. **Grayscale fallback** – never fails

This shows your understanding of **resilience and fault-tolerant design**.

---

## 🗄 Database Architecture (Supabase)

Includes:

* `images` table
* `image_metadata` table
* Row-Level Security (RLS) policies
* Full-text search index
* GIN indexes for tags

This demonstrates skills in **schema design** and **database optimization**.

---

## 📡 API Endpoints

Includes endpoints for:

* Auth (signup, login, refresh)
* Upload images
* Fetch metadata
* Search (tags, description, color)
* Similarity detection
* Signed image URLs
* CRUD operations

Clean URLs under `/api/v1/...`, showing attention to REST conventions.

---

## 🧪 Example Use Cases

* Upload an image → auto-analyzed → stored with metadata
* Search "sunset" → finds images tagged by AI
* Filter by orange color (#FF6B35)
* Retrieve similar images by color + tags + description
* Update display names
* Securely fetch signed URLs

---

## 🐳 Deployment Ready

* Dockerfile included
* Uvicorn workers for scaling
* Environment variables documented
* Works on local or cloud environments (Render, AWS, DigitalOcean)

---

## 💼 Why This Project Demonstrates Full-Stack Skills

This app proves:

### ✔ Backend architecture knowledge

Async API, routing, error handling, modular code.

### ✔ Database expertise

Indexes, RLS, search optimization, schema migrations.

### ✔ Security fundamentals

JWT auth, bcrypt, file validation, storage permissions.

### ✔ AI integration

Using GPT-4o Vision to extract structured and unstructured data.

### ✔ Cloud integration

Supabase storage, signed URLs, bucket policies.

### ✔ DevOps & deployment

Docker, environment variables, Uvicorn workers.

### ✔ Real-world engineering thinking

Fallback pipelines, cost analysis, search algorithms.

---

## 📝 Purpose of This Repository

This project was developed as a **technical portfolio piece** for applying to a **Full-Stack Developer position**.

It is designed to reflect:

* Production-ready code quality
* Strong understanding of backend systems
* Ability to integrate multiple modern technologies
* Engineering judgment and problem-solving
* Dependability and scalability considerations
