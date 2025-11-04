# 🧠 Pinecone Knowledge Base Setup Guide

## 📋 Overview

Pinecone is your agent's "brain" - it stores company information, FAQs, and knowledge that Clara can search through to answer customer questions.

**Required for:** All 3 agent variants (especially Variant 1: Basic Q&A)

**Setup Time:** 15 minutes

---

## 🎯 Step 1: Create Pinecone Account (5 minutes)

### 1.1 Sign Up

1. Go to: https://www.pinecone.io/
2. Click **"Start Free"** or **"Sign Up"**
3. Choose sign-up method:
   - Email + Password (recommended)
   - Google Account
   - GitHub Account

### 1.2 Verify Email

1. Check your email inbox
2. Click the verification link
3. Complete your profile

### 1.3 Choose Plan

**Select:** **Starter Plan (FREE)**
- ✅ 1 index included
- ✅ 100,000 vectors
- ✅ Perfect for getting started
- ✅ No credit card required

---

## 🗄️ Step 2: Create Your Index (5 minutes)

### 2.1 Access Dashboard

1. After login, you'll see the Pinecone Console
2. Click **"Create Index"** or **"+ Create Index"**

### 2.2 Configure Index

**Enter these EXACT values:**

| Field | Value | Why |
|-------|-------|-----|
| **Index Name** | `callisi-kb` | Must match .env configuration |
| **Dimensions** | `1536` | Azure OpenAI embedding size |
| **Metric** | `cosine` | Best for semantic search |
| **Cloud** | `AWS` | Free tier |
| **Region** | `us-east-1` | Free tier region |

**Important:** 
- Index name MUST be exactly `callisi-kb` (lowercase!)
- Dimensions MUST be exactly `1536`

### 2.3 Create Index

1. Click **"Create Index"**
2. Wait 30-60 seconds for index to be ready
3. Status will change to **"Ready"** (green)

---

## 🔑 Step 3: Get API Key (2 minutes)

### 3.1 Access API Keys

1. In Pinecone Console, click **"API Keys"** in left sidebar
2. You'll see your default API key already created

### 3.2 Copy API Key

1. Find your API key (starts with `pc-` or similar)
2. Click the **copy icon** 📋
3. Save it temporarily (you'll need it in next step)

### 3.3 Get Environment Name

1. On the same API Keys page
2. Look for **"Environment"** field
3. It will be something like: `us-east-1-aws` or `gcp-starter`
4. Copy this value too

---

## ⚙️ Step 4: Configure Agent (3 minutes)

### 4.1 Open .env File

Navigate to your agent folder and open `.env`:

```bash
cd "c:\lynn order\livekit-voice-agents_sanitized"
notepad .env
```

### 4.2 Add Pinecone Credentials

Find these lines and fill in your values:

```bash
# Pinecone Configuration
PINECONE_API_KEY=your-pinecone-api-key-here    # ← Paste your API key
PINECONE_ENV=us-east-1-aws                     # ← Paste your environment
PINECONE_INDEX=callisi-kb                      # ← Already correct!
```

**Example:**
```bash
PINECONE_API_KEY=pc-abc123xyz456def789
PINECONE_ENV=us-east-1-aws
PINECONE_INDEX=callisi-kb
```

### 4.3 Save File

1. Press `Ctrl+S` to save
2. Close the editor

---

## 📚 Step 5: Add Sample Knowledge (Optional - 10 minutes)

### 5.1 Create Sample FAQs Script

Create a Python script to upload sample company information:

```bash
cd "c:\lynn order\livekit-voice-agents_sanitized"
notepad upload_knowledge.py
```

**Paste this code:**

```python
import os
from pinecone import Pinecone
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index = pc.Index(os.getenv("PINECONE_INDEX"))

# Initialize Azure OpenAI for embeddings
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-08-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Sample company knowledge
knowledge = [
    {
        "id": "faq-1",
        "text": "Unsere Geschäftszeiten sind Montag bis Freitag von 9:00 bis 18:00 Uhr. Am Wochenende sind wir geschlossen.",
        "category": "hours"
    },
    {
        "id": "faq-2",
        "text": "Wir bieten Voice AI Lösungen für Unternehmen, einschließlich automatischer Anrufbeantwortung, Terminbuchung und Kundenservice.",
        "category": "services"
    },
    {
        "id": "faq-3",
        "text": "Kontaktieren Sie uns per E-Mail unter info@callisi.com oder rufen Sie uns an unter +49 xxx xxxx.",
        "category": "contact"
    },
    {
        "id": "faq-4",
        "text": "Unsere Preise beginnen bei 295€ pro Monat für das Basis-Paket. Kontaktieren Sie uns für ein individuelles Angebot.",
        "category": "pricing"
    },
    {
        "id": "faq-5",
        "text": "Ja, wir bieten DSGVO-konforme Lösungen an. Alle Daten werden in der EU verarbeitet und gespeichert.",
        "category": "compliance"
    }
]

print("Uploading knowledge to Pinecone...")

for item in knowledge:
    # Generate embedding
    response = client.embeddings.create(
        input=item["text"],
        model="text-embedding-ada-002"
    )
    embedding = response.data[0].embedding
    
    # Upload to Pinecone
    index.upsert(vectors=[{
        "id": item["id"],
        "values": embedding,
        "metadata": {
            "text": item["text"],
            "category": item["category"]
        }
    }])
    print(f"✅ Uploaded: {item['id']}")

print("\n✅ Done! Knowledge base is ready!")
print(f"Total items: {len(knowledge)}")
```

### 5.2 Run Upload Script

```bash
uv run python upload_knowledge.py
```

**Expected output:**
```
Uploading knowledge to Pinecone...
✅ Uploaded: faq-1
✅ Uploaded: faq-2
✅ Uploaded: faq-3
✅ Uploaded: faq-4
✅ Uploaded: faq-5

✅ Done! Knowledge base is ready!
Total items: 5
```

---

## ✅ Step 6: Test Knowledge Base (2 minutes)

### 6.1 Start Agent

```bash
uv run python agent_basic.py console
```

### 6.2 Test in LiveKit Playground

1. Go to: https://agents-playground.livekit.io/
2. Connect with your credentials
3. Use **Chat tab**
4. Ask: **"Was sind Ihre Öffnungszeiten?"** (What are your business hours?)

**Expected Response:**
Clara should respond with: "Unsere Geschäftszeiten sind Montag bis Freitag von 9:00 bis 18:00 Uhr..."

### 6.3 More Test Questions

Try these:
- "Welche Dienstleistungen bieten Sie an?" (What services do you offer?)
- "Wie kann ich Sie kontaktieren?" (How can I contact you?)
- "Was kostet Ihr Service?" (How much does your service cost?)

---

## 🎯 Adding Your Own Company Knowledge

### Method 1: Edit upload_knowledge.py

Add more items to the `knowledge` list:

```python
{
    "id": "faq-6",
    "text": "Your company information here in German...",
    "category": "your-category"
}
```

### Method 2: Upload Documents

For larger knowledge bases, you can:
1. Prepare documents (PDF, TXT, DOCX)
2. Use Pinecone's document upload tools
3. Or create a script to batch-upload

---

## 🐛 Troubleshooting

### Error: "Pinecone not configured"

**Solution:**
- Check `.env` file has all 3 Pinecone variables
- Verify no typos in variable names
- Restart agent after updating `.env`

### Error: "Index not found"

**Solution:**
- Index name must be exactly `callisi-kb`
- Check spelling in Pinecone Console
- Wait 1-2 minutes after creating index

### Error: "Dimensions mismatch"

**Solution:**
- Index must be created with 1536 dimensions
- If wrong, delete index and create new one
- Ensure using Azure OpenAI embeddings (not OpenAI directly)

### Agent doesn't use knowledge base

**Solution:**
- Verify upload script ran successfully
- Check Pinecone Console shows vectors uploaded
- Try more specific questions
- Ensure agent is using `query_kb` tool

---

## 📊 Monitoring Your Knowledge Base

### Check Vector Count

In Pinecone Console:
1. Click on your `callisi-kb` index
2. View **"Vector Count"**
3. Should match number of items uploaded

### View Index Stats

- Total vectors
- Index size
- Query statistics
- Recent activity

---

## 💡 Best Practices

### 1. **Organize by Category**
```python
metadata: {
    "text": "...",
    "category": "hours|services|contact|pricing",
    "priority": "high|medium|low"
}
```

### 2. **Use German Language**
- All knowledge should be in German
- Matches your customer base
- Clara responds in German

### 3. **Keep Text Concise**
- 1-3 sentences per item
- Clear and direct answers
- Avoid unnecessary details

### 4. **Update Regularly**
- Add new FAQs as they arise
- Update outdated information
- Remove obsolete content

### 5. **Test After Updates**
- Always test queries after adding knowledge
- Verify Clara finds and uses new information
- Adjust wording if needed

---

## 🎓 Advanced: Batch Upload

For uploading many items:

```python
# Create embeddings in batches
batch_size = 100
for i in range(0, len(knowledge), batch_size):
    batch = knowledge[i:i+batch_size]
    # Process batch...
```

---

## ✅ Completion Checklist

- [ ] Pinecone account created
- [ ] Index `callisi-kb` created (1536 dimensions)
- [ ] API key copied
- [ ] Environment name noted
- [ ] `.env` file updated
- [ ] Sample knowledge uploaded
- [ ] Agent tested with knowledge queries
- [ ] Clara responds with company information

**Once all checked: ✅ Pinecone is ready!**

---

## 📞 Need Help?

**Common Issues:**
- Index creation fails → Try different region
- Upload fails → Check API key is valid
- Agent doesn't search → Verify tool is enabled

**Resources:**
- Pinecone Docs: https://docs.pinecone.io/
- Azure OpenAI Embeddings: https://learn.microsoft.com/en-us/azure/ai-services/openai/

---

**Setup Complete! Your agent now has a knowledge base!** 🧠✅
