# AI Menu Reader

## Docker Setup for ai_menu_reader

### ✅ 5️⃣ Build Docker Image
```bash
cd ai_menu_reader
docker build -t ai-menu-reader .
```

### ✅ 6️⃣ Run Container
```bash
docker run --rm --env-file .env -p 8000:8000 ai-menu-reader
```

## Prerequisites
- Docker installed
- .env file with required API keys (SARVAM_API_KEY and gemini_API_KEY)