# 🎧 IndustryEar — Your AI Personal Advisor

**IndustryEar** is an AI-powered Personal Advisor (AI P.A) that monitors your industry, scans the entire internet for breakthroughs, filters out noise, and delivers only the most significant updates—instantly in natural-sounding audio.

---

## 🧠 What IndustryEar Does

IndustryEar turns overwhelming noise into actionable intelligence. It autonomously:
*   **Monitors** specific niches, keywords, companies, and market trends.
*   **Filters** massive information streams to detect early signals and hidden opportunities.
*   **Summarizes** complex news into polished, broadcast-style insights using the **Grok (xAI)** LLM.
*   **Synthesizes** insights into audio briefs for a hands-free experience.
*   **Delivers** updates directly to your WhatsApp, Email, or private Podcast feed.

---

## 🚀 Technical Stack

### Backend
*   **FastAPI**: High-performance Python framework for building APIs.
*   **Grok (xAI)**: Advanced LLM for intelligent news research and scriptwriting.
*   **LangChain & LangGraph**: Powering the autonomous research agents.
*   **RapidAPI**: Real-time news data retrieval.
*   **gTTS**: Google Text-to-Speech for audio synthesis.

### Frontend (Coming Soon)
*   **Next.js + TypeScript**
*   **Tailwind CSS + Shadcn/UI**
*   **Framer Motion** for premium animations.

---

## 🛠️ Getting Started

### 1. Prerequisites
*   Python 3.10+
*   API Keys for: xAI (Grok), RapidAPI, and optionally Tavily.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/Jayandhan03/Just-Know.git
cd Just-Know

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
XAI_API_KEY=your_grok_key
RAPID_API_KEY=your_rapidapi_key
TAVILY_API_KEY=your_tavily_key  # Optional for web search
```

### 4. Running the Server
```bash
uvicorn app.main:app --reload
```
Access the interactive documentation at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🛣️ API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/news/generate` | AI agent research & bullet-point summary |
| `POST` | `/api/v1/news/summarize` | RapidAPI fetch + Grok broadcast summary |
| `POST` | `/api/v1/audio/news` | Full pipeline: Fetch → Summarize → Stream MP3 |
| `GET` | `/api/v1/health` | Service health status |

---

## 📂 Project Structure

```text
IndustryEar/
├── app/
│   ├── api/          # Unified API routing
│   ├── core/         # Config & Logging
│   ├── models/       # Pydantic schemas
│   ├── services/     # News, LLM, and Audio logic
│   └── main.py       # App entry point
├── requirements.txt  # Production dependencies
└── README.md         # You are here
```

---

## 🌟 Why It Exists

**Information is abundant. Attention is scarce. Timing is everything.**

IndustryEar ensures you move faster and think smarter by delivering the intelligence you need the moment it matters.