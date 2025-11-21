# Quick Start Guide

Get MediGuard AI running in 5 minutes!

## Prerequisites Check

- [ ] Python 3.9+ installed (`python --version`)
- [ ] Node.js 18+ installed (`node --version`)
- [ ] Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

## Step-by-Step Setup

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd mediguard-ai
```

### 2. Backend Setup (Terminal 1)

```bash
# Install Python packages
pip install -r requirements.txt

# Create environment file
echo GOOGLE_API_KEY=your_api_key_here > .env
# Edit .env and replace 'your_api_key_here' with your actual key

# Start backend server
python api_server.py
```

You should see: `INFO: Uvicorn running on http://0.0.0.0:8000`

### 3. Frontend Setup (Terminal 2)

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

You should see: `Ready on http://localhost:3000`

### 4. Test It!

1. Open browser to `http://localhost:3000`
2. You'll see sample patient IDs listed
3. Click one or enter: `341de73b-56e5-6f58-c32f-9d56a1290e2f`
4. Click "Start Analysis"
5. Watch the workflow progress and see results!

## Troubleshooting

**Backend won't start?**
- Check Python version: `python --version` (need 3.9+)
- Check if port 8000 is in use
- Verify `.env` file exists with `GOOGLE_API_KEY`

**Frontend won't connect?**
- Make sure backend is running first
- Check browser console for errors
- Verify `PYTHON_API_URL` in frontend `.env.local` (defaults to localhost:8000)

**No patient data?**
- Ensure `data1/` folder has CSV files
- Check that patient IDs are UUIDs
- Verify CSV files are properly formatted

## Next Steps

- Read [Backend Documentation](BACKEND.md) to understand the agents
- Read [Frontend Documentation](FRONTEND.md) to customize the UI
- Check [Synthea Data Mapping](synthea-data-mapping.md) for data requirements

## Common Commands

```bash
# Backend
python api_server.py          # Start API server
python main.py <patient_id>   # Test individual analysis

# Frontend
npm run dev    # Development
npm run build  # Production build
npm run start  # Production server
```

