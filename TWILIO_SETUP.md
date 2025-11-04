# 📞 Twilio Configuration Guide

## 📋 Overview

This guide shows how to configure Twilio for phone integration with your voice agents.

**Required for:**
- ✅ Variant 2: Forward + SMS
- ✅ Variant 3: Forward + WhatsApp
- ❌ NOT required for Variant 1 (Basic)

**Setup Time:** 30 minutes

---

## 🎯 Step 1: Twilio Account Setup (5 minutes)

### 1.1 Create Account

1. Go to: https://www.twilio.com/
2. Click **"Sign Up"** or **"Try Twilio Free"**
3. Fill in details:
   - Email
   - Password
   - Phone number (for verification)

### 1.2 Verify Account

1. Check email for verification code
2. Enter code in Twilio Console
3. Verify your phone number with SMS code

### 1.3 Upgrade Account (If needed)

**Trial Account Limitations:**
- Can only call/SMS verified numbers
- Caller ID shows "Trial Account"

**To remove limitations:**
1. Add payment method (credit card)
2. Upgrade to paid account (~$20 minimum)
3. No monthly fees, pay-as-you-go

---

## 📱 Step 2: Buy a Phone Number (10 minutes)

### 2.1 Navigate to Phone Numbers

1. In Twilio Console, click **"Phone Numbers"**
2. Click **"Buy a number"**

### 2.2 Choose Number

**For Germany (Recommended for Callisi):**
1. Country: **Germany (+49)**
2. Capabilities needed:
   - ✅ **Voice** (required)
   - ✅ **SMS** (for Variant 2)
   - ✅ **MMS** (optional)
3. Click **"Search"**

**Pricing:**
- German numbers: ~€1-5/month
- Additional: ~€0.05/minute for calls

### 2.3 Purchase Number

1. Select a number you like
2. Click **"Buy"**
3. Confirm purchase
4. **Copy the number** (e.g., `+4915888648394`)

---

## 🔑 Step 3: Get API Credentials (5 minutes)

### 3.1 Account SID & Auth Token

1. In Twilio Console, go to **Dashboard** (home)
2. Find **"Account Info"** section
3. Copy these values:

| Field | Example | Description |
|-------|---------|-------------|
| **Account SID** | `ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` | Your account identifier |
| **Auth Token** | `your_auth_token_here` | Secret key (click "Show" to reveal) |

**⚠️ Keep Auth Token secret!** Never share publicly.

### 3.2 Add to .env File

Open your `.env` file and add:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+4915888648394
```

---

## 📞 Step 4: Configure SIP Trunk for Voice (15 minutes)

### 4.1 Create SIP Trunk

1. In Twilio Console, go to **"Elastic SIP Trunking"**
2. Click **"Trunks"** → **"Create new SIP Trunk"**
3. **Friendly Name:** `Callisi-LiveKit-Trunk`
4. Click **"Create"**

### 4.2 Add Origination URI

1. In your trunk, go to **"Origination"** tab
2. Click **"Add new Origination URI"**
3. Enter LiveKit SIP URI:

**Format:**
```
sip:YOUR_DISPATCH_ID@YOUR_DISPATCH_ID.sip.livekit.cloud
```

**To find YOUR_DISPATCH_ID:**
1. Go to LiveKit Console: https://cloud.livekit.io
2. Select your project
3. Go to **"SIP"** section
4. Look for **Dispatch Rule** or **SIP URI**
5. It looks like: `3i1153gfo0b` (random characters)

**Example:**
```
sip:3i1153gfo0b@3i1153gfo0b.sip.livekit.cloud
```

4. **Priority:** `10`
5. **Weight:** `10`
6. **Enabled:** ✅ Check
7. Click **"Add"**

### 4.3 Configure Termination

1. Go to **"Termination"** tab
2. Click **"Add new Termination URI"** (if needed)
3. Usually can leave default settings

### 4.4 Add Phone Number to Trunk

1. Go to **"Phone Numbers"** tab (in the trunk)
2. Click **"Add an existing number"**
3. Select the phone number you bought earlier
4. Click **"Add"**

---

## 🔗 Step 5: Connect Phone to LiveKit (10 minutes)

### 5.1 Configure Number Voice Settings

1. Go back to **"Phone Numbers"** → **"Manage Numbers"**
2. Click on your phone number
3. Scroll to **"Voice Configuration"**

### 5.2 Set Voice URL

**Configure these settings:**

| Field | Value |
|-------|-------|
| **A CALL COMES IN** | **TwiML Bin** (or **SIP**) |
| **Handler** | Select your SIP Trunk |
| **Primary Handler Fails** | Default |

**If using SIP directly:**
```
sip:YOUR_DISPATCH_ID@YOUR_DISPATCH_ID.sip.livekit.cloud
```

### 5.3 Save Configuration

1. Click **"Save"**
2. Wait 30 seconds for changes to propagate

---

## 💬 Step 6: Configure SMS (Variant 2 Only)

### 6.1 Enable SMS

1. Same phone number settings page
2. Scroll to **"Messaging Configuration"**

### 6.2 Set SMS Webhook (Optional)

**For SMS notifications:**
```bash
# In .env file
TWILIO_SMS_TO=+49-your-staff-phone-number
```

This is where SMS notifications will be sent when a human agent is unavailable.

---

## 💚 Step 7: Configure WhatsApp (Variant 3 Only)

### 7.1 WhatsApp Sandbox (Testing)

**For testing/development:**

1. In Twilio Console, go to **"Messaging"** → **"Try it out"** → **"Send a WhatsApp message"**
2. Follow instructions to join sandbox:
   - Send a WhatsApp message to Twilio's sandbox number
   - Format: `join [your-code]`
3. Note the sandbox number: `whatsapp:+14155238886`

### 7.2 Production WhatsApp (Optional)

**For production:**
1. Request WhatsApp Business profile
2. Get approved by Meta/Facebook
3. Can take 1-2 weeks

**For now, use sandbox for testing!**

### 7.3 Configure in .env

```bash
# WhatsApp Configuration (Variant 3)
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886          # Twilio sandbox number
TWILIO_WHATSAPP_TO=whatsapp:+49-your-phone-number  # Your WhatsApp
```

---

## ⚙️ Step 8: Configure Agent .env File

### Complete .env Configuration

**For Variant 2 (SMS):**
```bash
# Twilio for SMS
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+4915888648394
TWILIO_SMS_TO=+49-staff-phone-number

# SIP Configuration
DEFAULT_FORWARD_NUMBER=+49-human-agent-number
SIP_TRUNK_NAME=Callisi-LiveKit-Trunk
RING_TIMEOUT_SECONDS=25
```

**For Variant 3 (WhatsApp):**
```bash
# Twilio for WhatsApp
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
TWILIO_WHATSAPP_TO=whatsapp:+49-your-number

# SIP Configuration
DEFAULT_FORWARD_NUMBER=+49-human-agent-number
SIP_TRUNK_NAME=Callisi-LiveKit-Trunk
RING_TIMEOUT_SECONDS=25
```

---

## 🧪 Step 9: Testing

### 9.1 Test Basic Call

1. Call your Twilio number from your phone
2. Agent should answer
3. Have a conversation

**Expected:**
- ✅ Clara answers in German
- ✅ Understands your questions
- ✅ Responds naturally

### 9.2 Test Call Forwarding (Variants 2 & 3)

1. Call your Twilio number
2. Say: **"Ich möchte mit einem Menschen sprechen"** (I want to speak to a human)
3. Clara should say: "Einen Moment bitte, ich stelle Sie durch..."
4. Call should ring at `DEFAULT_FORWARD_NUMBER`

**Expected:**
- ✅ Clara attempts to forward
- ✅ Your configured number rings
- ✅ You can answer and talk to caller

### 9.3 Test SMS Fallback (Variant 2)

1. Call your Twilio number
2. Request human transfer
3. **DON'T answer** the forwarded call
4. Wait 25 seconds

**Expected:**
- ✅ SMS sent to `TWILIO_SMS_TO` number
- ✅ Message: "Clara: Ziel nicht erreicht... Bitte Rückruf an [caller]"
- ✅ Clara informs caller: "Ich habe das Team per SMS informiert..."

### 9.4 Test WhatsApp Fallback (Variant 3)

1. Same as SMS test
2. WhatsApp message should arrive instead
3. Check WhatsApp on `TWILIO_WHATSAPP_TO` number

---

## 📊 Monitoring & Logs

### Twilio Console Monitoring

1. Go to **"Monitor"** → **"Logs"** → **"Calls"**
2. See all incoming/outgoing calls
3. Duration, status, recordings
4. Click call for detailed logs

### View Call Recordings (Optional)

1. Enable call recording in phone number settings
2. Recordings appear in Monitor → Calls
3. Can download or play in browser

### Check SMS/WhatsApp Logs

1. **"Monitor"** → **"Logs"** → **"Messages"**
2. See all SMS/WhatsApp sent
3. Delivery status
4. Error messages if any

---

## 💰 Cost Estimates

### Typical Costs (Germany):

| Item | Cost | Notes |
|------|------|-------|
| **Phone Number** | €1-5/month | Depends on number type |
| **Incoming Calls** | ~€0.05/min | Standard rate |
| **Outgoing Calls** | ~€0.05/min | For forwarding |
| **SMS** | ~€0.05/SMS | Per message sent |
| **WhatsApp** | Free (sandbox) | Production: varies |

**Example monthly cost:**
- 100 calls × 2 min avg = €10
- 20 SMS notifications = €1
- Phone number = €2
- **Total: ~€13/month**

---

## 🐛 Troubleshooting

### Phone doesn't ring

**Check:**
- ✅ Phone number is active in Twilio
- ✅ SIP trunk configured correctly
- ✅ LiveKit dispatch ID is correct
- ✅ Number is connected to trunk

**Solution:**
1. Check Twilio logs for errors
2. Verify SIP URI format
3. Test trunk connection

### Agent doesn't answer

**Check:**
- ✅ Agent is running (`uv run python agent_forward_sms.py start`)
- ✅ LiveKit shows agent as connected
- ✅ No errors in agent logs

**Solution:**
1. Restart agent
2. Check LiveKit Console for agent status
3. Verify credentials in `.env`

### Call forwarding doesn't work

**Check:**
- ✅ `DEFAULT_FORWARD_NUMBER` is valid
- ✅ Format: `+49xxxxxxxxxx` (with country code)
- ✅ SIP trunk allows outbound calls
- ✅ `request_human_transfer` tool is enabled

**Solution:**
1. Verify phone number format
2. Check Twilio outbound call logs
3. Enable outbound in SIP trunk settings

### SMS not received

**Check:**
- ✅ `TWILIO_SMS_TO` is correct
- ✅ Format includes country code: `+49...`
- ✅ Number is SMS-capable
- ✅ Account has SMS credits

**Solution:**
1. Check Twilio message logs
2. Verify number format
3. Test with a different number

### WhatsApp not received

**Check:**
- ✅ You joined WhatsApp sandbox
- ✅ Using correct sandbox number
- ✅ `TWILIO_WHATSAPP_TO` format: `whatsapp:+49...`
- ✅ WhatsApp is installed on phone

**Solution:**
1. Re-join sandbox (send "join" message again)
2. Check Twilio message logs
3. Verify WhatsApp number format

---

## ✅ Completion Checklist

**Twilio Account:**
- [ ] Account created and verified
- [ ] Payment method added (if needed)
- [ ] Phone number purchased

**SIP Trunk:**
- [ ] SIP trunk created
- [ ] Origination URI configured with LiveKit
- [ ] Phone number added to trunk

**Configuration:**
- [ ] `.env` file updated with credentials
- [ ] `DEFAULT_FORWARD_NUMBER` set
- [ ] SMS/WhatsApp numbers configured

**Testing:**
- [ ] Basic call works (Clara answers)
- [ ] Call forwarding tested
- [ ] SMS fallback tested (Variant 2)
- [ ] WhatsApp fallback tested (Variant 3)

**Once all checked: ✅ Twilio is ready!**

---

## 📞 Advanced Features

### Call Recording

```bash
# In phone number settings:
- Enable "Record Calls"
- Recording notification: "This call may be recorded..."
```

### Call Screening

```bash
# Add screening before agent answers:
- Use TwiML to play message first
- Route to agent after screening
```

### Business Hours

```bash
# Route calls differently based on time:
- Business hours → Agent
- After hours → Voicemail
- Configure in TwiML
```

---

## 🎓 Resources

- Twilio SIP Trunking Docs: https://www.twilio.com/docs/sip-trunking
- LiveKit SIP Integration: https://docs.livekit.io/sip/
- WhatsApp Business API: https://www.twilio.com/whatsapp
- Twilio Console: https://console.twilio.com/

---

**Setup Complete! Your agent can now handle phone calls!** 📞✅
