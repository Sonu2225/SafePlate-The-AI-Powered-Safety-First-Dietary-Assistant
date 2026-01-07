# SafePlate: The AI-Powered Safety-First Dietary Assistant

**SafePlate** is a smart, conversational recipe assistant designed to
help users find meals that fit their specific dietary needs while
prioritizing safety. Unlike standard AI chatbots that can hallucinate
ingredients, SafePlate uses a **Hybrid RAG (Retrieval-Augmented
Generation)** architecture to enforce strict allergen exclusion and
accurate calorie limits.

##  Key Features

### ️ Safety Gate

A deterministic filter (**Service B**) physically isolates the AI from
unsafe data. It uses **SQLite FTS5** to mathematically exclude allergens
before the AI ever sees the recipe.

###  Hybrid AI

Uses **Gemini 2.5 Flash** for high-speed keyword extraction and **Gemini
2.5 Pro** for intelligent, reasoning-based recipe generation.

###  Secure Auth

User accounts are protected with **Bcrypt password hashing** and include
a secure, SMTP-based **Forgot Password** flow.

###  Personalized Profiles

Persists user allergies, calorie limits, and cuisine preferences in a
secure database across sessions.

###  Containerized

The entire application (Frontend + 3 Backend Services) is fully
**Dockerized** for easy deployment.

###  Automated Safety

Includes a **CI/CD pipeline (GitHub Actions)** that runs regression
tests on every push to ensure the Safety Gate is never broken.


## ️ Architecture

SafePlate follows a **Microservices Architecture**:

-   **Service A (Auth)** --- User registration, login, profile
    management, SMTP emails\
    *Port 5000*

-   **Service B (Data / Safety Gate)** --- Manages 13,000+ recipes and
    enforces strict SQL filtering\
    *Port 5001*

-   **Service C (Orchestrator / Brain)** --- Connects user requests to
    Service B and Google Gemini\
    *Port 5002*

-   **Frontend** --- React SPA built with Vite and Tailwind CSS\
    *Port 5173*

##  Tech Stack

**Frontend** - React - Vite - Tailwind CSS

**Backend** - Python - Flask

**Database** - SQLite - FTS5 (Full-Text Search)

**AI Engine** - Google Gemini (Flash & Pro)

**Infrastructure** - Docker - Docker Compose

**Testing & CI** - Python unittest - GitHub Actions

## Getting Started

### Prerequisites

-   Docker Desktop (running)
-   Git

### Installation & Run

#### Clone the repository

``` bash
git clone https://github.com/YourUsername/recipe-helper.git
cd recipe-helper
```

#### Create environment variables

Create a `.env` file in the root directory:

``` env
GOOGLE_API_KEY=your_gemini_api_key
MAIL_USERNAME=your_gmail_address
MAIL_PASSWORD=your_app_password
```

#### Run with Docker

``` bash
docker-compose up --build
```

#### Access the app

Open your browser at:\
http://localhost:5173

## Security

### Zero-Trust Isolation

The AI service (**Service C**) has **no direct database access**. All
data must flow through **Service B**.

### Data Protection

User allergies are stored in a dedicated `SecureUserProfile.db`,
isolated from public recipe data.


## Testing

Automated tests live in:

    tests/test_safety.py

They run on every push via **GitHub Actions**.

-   **Red Team Testing** --- Attempts unsafe ingredient requests and
    expects zero results\
-   **Calorie Checks** --- Ensures recipes strictly respect user calorie
    limits

##  Disclaimer: API Limits

This project uses **Google Gemini 2.5 Pro** for high-quality recipe
synthesis and safety reasoning.

-   **Daily Token Limits** apply under the Gemini Free Tier\
-   **Rate Limiting** may cause temporary delays under heavy usage

The system implements **exponential backoff**, but extensive testing may
temporarily exhaust the quota.


