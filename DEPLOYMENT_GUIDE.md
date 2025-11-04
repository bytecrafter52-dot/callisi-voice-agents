# 🚀 Voice Agent Deployment Guide

## 📋 Overview

This project contains **3 agent variants** for different use cases:

| Variant | File | Use Case | Features |
|---------|------|----------|----------|
| **Variant 1** | `agent_basic.py` | Basic Q&A | Pinecone KB only, no forwarding |
| **Variant 2** | `agent_forward_sms.py` | Q&A + SMS fallback | Forwarding + SMS notification |
| **Variant 3** | `agent_forward_whatsapp.py` | Q&A + WhatsApp fallback | Forwarding + WhatsApp notification |

---

## 🎯 Choose Your Variant

### Variant 1: Basic Q&A Agent (`agent_basic.py`)

**Best for:**
- Simple customer service queries
- FAQ answering
- No need for human escalation

**Features:**
- ✅ Azure OpenAI for conversations
- ✅ Pinecone knowledge base
- ✅ German language support
- ❌ No call forwarding
- ❌ No SMS/WhatsApp

**When to use:**
- Initial testing
- Pure information queries
- Low-touch customer service

---

### Variant 2: Forward + SMS (`agent_forward_sms.py`)

**Best for:**
- Customer service with escalation
- Business hours support
- SMS-friendly customers

**Features:**
- ✅ All Basic features
- ✅ Call forwarding to human agents
- ✅ SMS notification if human unavailable
- ❌ No WhatsApp

**When to use:**
- Professional business environment
- Customers prefer SMS
- Need human backup

---

### Variant 3: Forward + WhatsApp (`agent_forward_whatsapp.py`)

**Best for:**
- Modern customer service
- International customers
- Rich media support

**Features:**
- ✅ All Basic features
- ✅ Call forwarding to human agents
- ✅ WhatsApp notification if human unavailable
- ✅ Full feature set

**When to use:**
- WhatsApp-friendly audience
- International business
- Modern communication preferred

---

## 📦 Prerequisites

### 1. **Azure Services** (Required for all variants)
- Azure Speech Services account
- Azure OpenAI deployment
- Region: Germany West Central (for GDPR)

### 2. **LiveKit Cloud** (Required for all variants)
- LiveKit project created
- API Key & Secret
- Webhook secret

### 3. **Pinecone** (Required for all variants)
- Free tier account
- Index created (name: `callisi-kb`)
- Dimensions: 1536 (for Azure OpenAI embeddings)

### 4. **Twilio** (Required for Variant 2 & 3 only)
- Account SID & Auth Token
- Phone number purchased
- WhatsApp sandbox configured (Variant 3 only)

---

## 🔧 Environment Setup

### Step 1: Copy Environment File

```bash
cp .env.example .env
```

### Step 2: Fill in Credentials

Edit `.env` and add your credentials:

#### **For ALL Variants:**

```bash
# LiveKit
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Azure Speech
AZURE_SPEECH_KEY=your-azure-speech-key
AZURE_SPEECH_REGION=germanywestcentral

# Azure OpenAI
AZURE_OPENAI_API_KEY=your-azure-openai-key
AZURE_OPENAI_ENDPOINT=https://your-name.openai.azure.com
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4.1-mini
AZURE_OPENAI_API_VERSION=2024-08-01-preview

# Pinecone
PINECONE_API_KEY=your-pinecone-key
PINECONE_ENV=your-pinecone-environment
PINECONE_INDEX=callisi-kb
```

#### **Additional for Variant 2 (SMS):**

```bash
# Twilio for SMS
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_SMS_TO=+49-target-phone

# SIP Configuration
DEFAULT_FORWARD_NUMBER=+49-human-agent-number
SIP_TRUNK_NAME=your-sip-trunk
RING_TIMEOUT_SECONDS=25
```

#### **Additional for Variant 3 (WhatsApp):**

```bash
# Twilio for WhatsApp
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+49-your-number

# SIP Configuration
DEFAULT_FORWARD_NUMBER=+49-human-agent-number
SIP_TRUNK_NAME=your-sip-trunk
RING_TIMEOUT_SECONDS=25
```

---

## 🚀 Local Testing

### Install Dependencies

```bash
# Using UV (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### Test Each Variant

#### **Variant 1: Basic**
```bash
uv run python agent_basic.py console
```

#### **Variant 2: Forward + SMS**
```bash
uv run python agent_forward_sms.py console
```

#### **Variant 3: Forward + WhatsApp**
```bash
uv run python agent_forward_whatsapp.py console
```

**Note:** Console mode may have audio issues on Windows. This is normal and doesn't affect production deployment.

---

## 📤 Production Deployment

### Option 1: Railway (Recommended)

1. **Install Railway CLI:**
```bash
npm install -g @railway/cli
```

2. **Login to Railway:**
```bash
railway login
```

3. **Initialize Project:**
```bash
railway init
```

4. **Deploy Variant:**

For **Variant 1 (Basic)**:
```bash
railway up --service agent-basic
```

For **Variant 2 (SMS)**:
```bash
railway up --service agent-sms
```

For **Variant 3 (WhatsApp)**:
```bash
railway up --service agent-whatsapp
```

5. **Set Environment Variables:**
```bash
# Copy all .env variables to Railway
railway variables set LIVEKIT_URL=wss://...
railway variables set AZURE_SPEECH_KEY=...
# ... repeat for all variables
```

6. **Start Agent:**
```bash
railway run python agent_basic.py start
# OR
railway run python agent_forward_sms.py start
# OR
railway run python agent_forward_whatsapp.py start
```

---

### Option 2: Docker Deployment

1. **Build Image:**
```bash
docker build -t callisi-agent-basic -f Dockerfile .
```

2. **Run Container:**
```bash
docker run -d \
  --name callisi-agent \
  --env-file .env \
  callisi-agent-basic \
  python agent_basic.py start
```

---

### Option 3: Render.com

1. **Create Web Service**
2. **Connect GitHub repo**
3. **Set Build Command:** `uv sync`
4. **Set Start Command:** 
   - Variant 1: `uv run python agent_basic.py start`
   - Variant 2: `uv run python agent_forward_sms.py start`
   - Variant 3: `uv run python agent_forward_whatsapp.py start`
5. **Add Environment Variables** from `.env`

---

## 📞 Connecting to Twilio

### Step 1: Buy Phone Number

1. Go to Twilio Console → Phone Numbers
2. Buy a number with Voice capabilities
3. Note the number (e.g., `+4915888648394`)

### Step 2: Configure SIP Trunk

1. Go to Elastic SIP Trunking → Create new trunk
2. Note the SIP URI from LiveKit
3. Add Origination URI: `sip:your-id@your-id.sip.livekit.cloud`

### Step 3: Route Calls to Agent

1. Go to your phone number settings
2. Voice Configuration → "A Call Comes In"
3. Select: **SIP**
4. Enter SIP URI: `sip:your-id@your-id.sip.livekit.cloud`
5. Save

---

## 🧪 Testing

### Test Basic Agent (Variant 1)

1. Deploy agent
2. Call the Twilio number
3. Ask: "Was sind Ihre Öffnungszeiten?" (What are your business hours?)
4. Agent should search knowledge base and respond

### Test Forward + SMS (Variant 2)

1. Deploy agent
2. Call the Twilio number
3. Say: "Ich möchte mit einem Menschen sprechen" (I want to speak to a human)
4. Agent should attempt to forward
5. If nobody answers within 25s → SMS sent to configured number

### Test Forward + WhatsApp (Variant 3)

1. Deploy agent
2. Call the Twilio number
3. Say: "Kann ich mit jemandem sprechen?" (Can I speak to someone?)
4. Agent should attempt to forward
5. If nobody answers within 25s → WhatsApp message sent

---

## 📊 Monitoring

### Check Agent Logs

```bash
# Railway
railway logs

# Docker
docker logs callisi-agent

# Local
# Logs appear in console
```

### Monitor in LiveKit Cloud

1. Go to https://cloud.livekit.io
2. Select your project
3. View active rooms and participants
4. Check agent connection status

---

## 🐛 Troubleshooting

### Agent Won't Start

**Check:**
- ✅ All environment variables set correctly
- ✅ API keys are valid
- ✅ Pinecone index exists
- ✅ Azure services are active

### No Voice Output

**Check:**
- ✅ Azure Speech credentials correct
- ✅ Region is `germanywestcentral`
- ✅ LiveKit SIP configuration correct

### Forwarding Not Working

**Check:**
- ✅ `DEFAULT_FORWARD_NUMBER` is valid
- ✅ SIP trunk configured in LiveKit
- ✅ Twilio SIP trunk active

### SMS/WhatsApp Not Sending

**Check:**
- ✅ Twilio credentials correct
- ✅ Phone number has SMS/WhatsApp capability
- ✅ WhatsApp sandbox approved (for Variant 3)

---

## 📚 Additional Resources

- [LiveKit Agents Documentation](https://docs.livekit.io/agents/)
- [Azure Speech Services](https://azure.microsoft.com/en-us/products/ai-services/ai-speech)
- [Twilio Voice Documentation](https://www.twilio.com/docs/voice)
- [Pinecone Documentation](https://docs.pinecone.io/)

---

## 🆘 Support

For issues or questions:
1. Check logs first
2. Verify all environment variables
3. Test individual services (Azure, Twilio, LiveKit)
4. Consult the main `README.md`

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
