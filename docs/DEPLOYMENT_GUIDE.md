# Deployment Guide - Full Agent Support

This guide shows how to deploy your RAG chatbot with **all 7 tools** including the web agent (Playwright) on various platforms.

---

## 🎯 Quick Comparison

| Platform | Difficulty | Free Tier | Web Agent | Best For |
|----------|-----------|-----------|-----------|----------|
| **Railway** | ⭐ Easy | $5 credit/mo | ✅ Yes | Quick deploys |
| **Render** | ⭐⭐ Easy | 750 hrs/mo | ✅ Yes | Production apps |
| **Fly.io** | ⭐⭐ Medium | 3 VMs | ✅ Yes | Global apps |
| **HF Spaces** | ⭐ Easy | Unlimited* | ✅ Yes | ML demos |
| **Cloud Run** | ⭐⭐⭐ Medium | 2M req/mo | ✅ Yes | Enterprise |
| **Streamlit Cloud** | ⭐ Easy | Unlimited | ❌ No | Basic RAG only |

*Public apps only

---

## 🚀 Option 1: Railway (Recommended - Easiest)

### Why Railway?
- Simplest deployment process
- $5 free credit/month
- Auto-deploys from GitHub
- Perfect for personal projects

### Steps:

1. **Sign up at Railway**
   - Go to https://railway.app
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose `ar-aishwaryanand-glitch/rag-chatbot`

3. **Add Environment Variables**
   ```
   GROQ_API_KEY=your_groq_api_key_here
   LLM_PROVIDER=groq
   GROQ_MODEL=llama-3.3-70b-versatile
   EMBEDDING_PROVIDER=huggingface
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

4. **Deploy**
   - Railway auto-detects Dockerfile
   - Builds and deploys automatically
   - Get your URL: `https://your-app.up.railway.app`

**Done! All 7 tools working.** 🎉

---

## 🚀 Option 2: Render (Recommended - Most Reliable)

### Why Render?
- More stable than Railway
- Better for production
- 750 hours free tier
- $7/month for paid tier

### Steps:

1. **Sign up at Render**
   - Go to https://render.com
   - Sign in with GitHub

2. **Deploy with Blueprint**
   - Go to https://render.com/deploy
   - Your repo has `render.yaml` - Render will use it automatically

   **OR manually:**
   - Click "New +" → "Web Service"
   - Connect `ar-aishwaryanand-glitch/rag-chatbot`
   - Select "Docker" as environment

3. **Configure**
   - Name: `rag-chatbot-agent`
   - Region: Choose closest to you
   - Branch: `main`
   - Dockerfile path: `./Dockerfile`
   - Plan: Free (or Starter for $7/mo)

4. **Add Environment Variables**
   Go to "Environment" tab and add:
   ```
   GROQ_API_KEY=your_groq_api_key_here
   LLM_PROVIDER=groq
   GROQ_MODEL=llama-3.3-70b-versatile
   EMBEDDING_PROVIDER=huggingface
   EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait 5-10 minutes for build
   - Get your URL: `https://rag-chatbot-agent.onrender.com`

**Free tier notes:**
- Sleeps after 15 min inactivity
- Takes 30-60s to wake up
- Upgrade to $7/month for always-on

---

## 🚀 Option 3: Fly.io (Good for Global Apps)

### Steps:

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login**
   ```bash
   fly auth login
   ```

3. **Launch App**
   ```bash
   fly launch
   ```

   - App name: `rag-chatbot-agent`
   - Region: Choose closest
   - Skip database setup

4. **Set Secrets**
   ```bash
   fly secrets set GROQ_API_KEY=your_groq_api_key_here
   fly secrets set LLM_PROVIDER=groq
   fly secrets set GROQ_MODEL=llama-3.3-70b-versatile
   fly secrets set EMBEDDING_PROVIDER=huggingface
   fly secrets set EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

**URL**: `https://rag-chatbot-agent.fly.dev`

---

## 🚀 Option 4: Hugging Face Spaces

### Steps:

1. **Create New Space**
   - Go to https://huggingface.co/spaces
   - Click "Create new Space"
   - Name: `rag-chatbot-agent`
   - SDK: Docker
   - Visibility: Public (free) or Private ($25/mo)

2. **Push Code**
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USERNAME/rag-chatbot-agent
   git push hf main
   ```

3. **Add Secrets**
   - In Space settings → "Repository secrets"
   - Add all environment variables

**URL**: `https://huggingface.co/spaces/YOUR_USERNAME/rag-chatbot-agent`

---

## 🚀 Option 5: Google Cloud Run

### Steps:

1. **Install gcloud CLI**
   ```bash
   brew install google-cloud-sdk  # Mac
   # Or download from https://cloud.google.com/sdk/docs/install
   ```

2. **Login & Setup**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Build & Push Image**
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/rag-chatbot
   ```

4. **Deploy**
   ```bash
   gcloud run deploy rag-chatbot-agent \
     --image gcr.io/YOUR_PROJECT_ID/rag-chatbot \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GROQ_API_KEY=your_key_here,LLM_PROVIDER=groq,GROQ_MODEL=llama-3.3-70b-versatile
   ```

**URL**: Provided after deployment

---

## 🐳 Local Docker Testing

Before deploying, test locally:

```bash
# Build image
docker build -t rag-chatbot:latest .

# Run container
docker run -p 8503:8503 \
  -e GROQ_API_KEY=your_key_here \
  -e LLM_PROVIDER=groq \
  -e GROQ_MODEL=llama-3.3-70b-versatile \
  -e EMBEDDING_PROVIDER=huggingface \
  -e EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2 \
  rag-chatbot:latest

# Open http://localhost:8503
```

---

## 📊 Cost Comparison

### Monthly Costs (Estimated)

| Platform | Free Tier | Paid Tier | Notes |
|----------|-----------|-----------|-------|
| Railway | $5 credit | Pay-as-you-go | ~$5-15/mo typical |
| Render | 750 hrs | $7/mo fixed | Best value for always-on |
| Fly.io | 3 VMs free | Pay-as-you-go | ~$5-10/mo typical |
| HF Spaces | Unlimited (public) | $25/mo (private) | Good for demos |
| Cloud Run | 2M requests | Pay-per-use | $0-20/mo depending on traffic |
| Streamlit Cloud | Unlimited | N/A | No web agent support |

---

## ✅ Post-Deployment Checklist

After deploying:

1. **Test All Tools**
   - Document search
   - Web search
   - Web agent (visit URL)
   - Calculator
   - Code executor
   - File operations
   - Document manager

2. **Check Memory**
   - Enable memory in sidebar
   - Test conversation continuity
   - Verify episodic memory saves

3. **Monitor Performance**
   - Check response times
   - Monitor memory usage
   - Review error logs

4. **Set Up Monitoring** (Production)
   - Add error tracking (Sentry)
   - Set up uptime monitoring
   - Configure alerts

---

## 🔧 Troubleshooting

### Playwright Install Fails
```bash
# In Dockerfile, ensure these are present:
playwright install chromium
playwright install-deps chromium
```

### Out of Memory
```bash
# Increase memory limit (Railway/Render)
# Or optimize embedding model in .env:
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Smaller model
```

### Build Takes Too Long
```bash
# Use smaller base image
FROM python:3.11-slim  # Already optimized in Dockerfile
```

### Port Issues
```bash
# Ensure Streamlit uses platform's PORT
CMD streamlit run ... --server.port=$PORT
```

---

## 📚 Additional Resources

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Playwright in Docker](https://playwright.dev/docs/docker)
- [Streamlit Deployment](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

## 🎉 Recommended Path

For most users:

1. **Start with Railway** - Easiest, $5 credit
2. **Move to Render** - When ready for production ($7/mo)
3. **Scale to Cloud Run** - When you need enterprise features

All platforms support the full 7-tool agent with web browsing! 🚀

---

*Last updated: 2026-02-02*
