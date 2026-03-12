# Power Automate Flow Construction Guide

> **Version:** 2.1.0
> **App:** Formación Evaluation Splitter
> **Last Updated:** 2026-03-12

---

## Overview

This document provides a complete guide for building the Power Automate flow that handles email sending for the Formación Evaluation Splitter app. The v2.1.0 flow supports:

- **Rich HTML email body** with full inline style preservation
- **CID-based inline images** (screenshots, logos, editor images)
- **Base64 data URI images** embedded directly in the HTML body (no CID, no inline attachments)
- **Single Excel attachment** — only one attachment field needed
- **Clean HTML layout** without card borders for natural email appearance

---

## 1. Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  Power Automate Flow                             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Trigger: "When an HTTP request is received"            │    │
│  │  Method: POST                                           │    │
│  │  JSON Schema: see Section 3                             │    │
│  └─────────────────────┬───────────────────────────────────┘    │
│                         │                                        │
│  ┌─────────────────────▼───────────────────────────────────┐    │
│  │  Action: "Send an email (V2)" — Office 365 Outlook      │    │
│  │                                                          │    │
│  │  To:          triggerBody()?['to']                       │    │
│  │  Subject:     triggerBody()?['subject']                  │    │
│  │  Body:        triggerBody()?['body']           (HTML)    │    │
│  │  CC:          triggerBody()?['cc']                       │    │
│  │  IsHtml:      true                                       │    │
│  │  Attachments: Excel only (attachmentName/Content)│    │
│  │  (Images embedded as data URIs in HTML body)    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Step-by-Step Construction

### Step 1: Create a New Instant Cloud Flow

1. Go to [Power Automate](https://make.powerautomate.com)
2. Click **"+ Create"** → **"Instant cloud flow"**
3. Name: `Formacion Email Sender v2`
4. Select trigger: **"When an HTTP request is received"**
5. Click **"Create"**

### Step 2: Configure the HTTP Trigger

1. Click on the trigger card
2. Set **Method** to `POST`
3. Paste the JSON schema from Section 3 below into the **"Request Body JSON Schema"** field
4. Save — the **HTTP POST URL** will be generated automatically

### Step 3: Add Send Email Action

1. Click **"+ New step"**
2. Search for **"Send an email (V2)"** (Office 365 Outlook)
3. Configure the fields as shown in Section 4

### Step 4: Save & Test

1. Save the flow
2. Copy the **HTTP POST URL** from the trigger
3. Set it in the `.env` file of the app: `POWER_AUTOMATE_URL=<copied_url>`
4. Test with the app's test mode

---

## 3. HTTP Trigger JSON Schema

```json
{
    "type": "object",
    "properties": {
        "to": {
            "type": "string",
            "description": "Recipient email address"
        },
        "cc": {
            "type": "string",
            "description": "CC email addresses separated by semicolons"
        },
        "subject": {
            "type": "string",
            "description": "Email subject line"
        },
        "body": {
            "type": "string",
            "description": "HTML email body with images embedded as base64 data URIs"
        },
        "isHtml": {
            "type": "boolean",
            "description": "Always true for this app"
        },
        "attachmentName": {
            "type": "string",
            "description": "Excel attachment filename"
        },
        "attachmentContent": {
            "type": "string",
            "description": "Excel attachment base64-encoded content"
        }
    },
    "required": ["to", "subject", "body", "isHtml"]
}
```

---

## 4. Email Action Configuration

### 4.1 Basic Fields

| Field | Expression | Notes |
|-------|-----------|-------|
| **To** | `@{triggerBody()?['to']}` | Single email address |
| **Subject** | `@{triggerBody()?['subject']}` | Already substituted with Tutor name |
| **Body** | `@{triggerBody()?['body']}` | Full HTML document — DO NOT modify |
| **CC** | `@{triggerBody()?['cc']}` | Semicolon-separated list |
| **Importance** | Normal | Can be customized |

### 4.2 Attachments Configuration (v2.1.0 — Excel Only)

Only the Excel file is sent as an attachment. Screenshots and editor images are embedded directly as base64 data URIs in the HTML body.

In the "Send an email (V2)" action's **Attachments** section, click **"Add new item"**:

| Attachment field | Expression |
|-----------------|------------|
| **Name** | `@{triggerBody()?['attachmentName']}` |
| **Content** | `@{base64ToBinary(triggerBody()?['attachmentContent'])}` |

> **Important:** The Content field must use `base64ToBinary()` to convert the base64 string into actual binary data.

### 4.3 Image Embedding Strategy

Screenshots and editor-inserted images are embedded as **base64 data URIs** directly in the HTML body:

```html
<img src="data:image/png;base64,iVBORw0KGgo..." style="max-width:100%;">
```

This approach:
- **No CID attachments needed** — images are self-contained in the HTML
- **No extra Power Automate configuration** — just pass the body through as-is
- **Works in Outlook Desktop, Web, and Mobile** (Office 365 environment)
- **Simplest flow** — only one attachment (Excel), everything else is in the body

---

## 5. Payload Examples

### 5.1 Full Payload (v2.1.0)

```json
{
  "to": "tutor@example.com",
  "cc": "manager@example.com;hr@example.com",
  "subject": "Evaluación Formación — Juan Berral",
  "body": "<!DOCTYPE html>...<img src='data:image/png;base64,iVBORw0KGgo...'>...</html>",
  "isHtml": true,
  "attachmentName": "Juan_Berral_evaluaciones.xlsx",
  "attachmentContent": "UEsDBBQAAAAI...(base64 Excel)"
}
```

### 5.2 Payload Fields

| Field | Purpose | Power Automate mapping |
|-------|---------|----------------------|
| `to` | Recipient email | To field |
| `cc` | CC emails (semicolon-separated) | CC field |
| `subject` | Email subject | Subject field |
| `body` | Full HTML with embedded data URI images | Body field |
| `isHtml` | Always `true` | (implicit) |
| `attachmentName` | Excel filename | Attachment → Name |
| `attachmentContent` | Excel base64 content | Attachment → `base64ToBinary()` → Content |

---

## 6. HTML Body Structure

The email body sent by v2.1.0 is a complete HTML document with:

1. **Full HTML document** with `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` tags
2. **Clean white background** without card borders or shadows for natural appearance
3. **All styles inline** (no `<style>` blocks, no CSS classes)
4. **CID image references** instead of base64 data-URIs

```html
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Evaluación Formación — {{tutor_name}}</title>
</head>
<body style="margin:0; padding:0; background-color:#ffffff; font-family:Calibri,Arial,Helvetica,sans-serif; line-height:1.6; color:#333333;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#ffffff;">
    <tr>
      <td style="padding:24px 32px;">
        <!-- Editor content with inline styles goes here -->
        <!-- Images embedded as: <img src="data:image/png;base64,..."> -->
      </td>
    </tr>
  </table>
</body>
</html>
```

---

## 7. Email Client Compatibility

### Supported Features

| Feature | Outlook (Desktop) | Outlook (Web) | Gmail | Apple Mail |
|---------|:-:|:-:|:-:|:-:|
| Inline styles | ✅ | ✅ | ✅ | ✅ |
| Table layout | ✅ | ✅ | ✅ | ✅ |
| Base64 data URI images | ✅ | ✅ | ❌ | ✅ |
| Custom fonts | ✅ | ✅ | ⚠️ | ✅ |
| Background colors | ✅ | ✅ | ✅ | ✅ |

### Why Base64 Data URIs?

| Approach | Pros | Cons |
|----------|------|------|
| **Base64 data-URI** | Self-contained, no attachment config needed, simplest Power Automate setup | Not supported in Gmail; increases body size |
| **CID attachment** | Universally supported by email clients | Requires Power Automate to set Content-ID/IsInline correctly (unreliable via standard connector) |
| **External URL** | Small payload | Requires hosting, may be blocked by firewalls |

The app uses **base64 data URIs** because the target recipients use Outlook (Office 365 corporate environment), and this approach avoids the Power Automate CID configuration issues entirely.

---

## 8. Troubleshooting

### Issue: Excel attachment cannot be opened

**Cause:** The Excel content was not reaching the connector as actual file bytes.

**Fix:** Ensure Attachment 1 uses `@{triggerBody()?['attachmentName']}` for Name and `@{triggerBody()?['attachmentContent']}` for Content. The content is base64-encoded by the app — the connector decodes it automatically.

---

### Issue: Images not displaying in email

1. Verify the app is running v2.1.0+ which embeds images as base64 data URIs in the HTML body
2. Check that `body` field in Power Automate is passed through as-is (no HTML sanitization)
3. If images are very large, check that the Power Automate HTTP trigger payload isn't hitting size limits
4. Data URI images work in Outlook Desktop/Web/Mobile but NOT in Gmail

### Issue: Visible side borders / card frame around email

**Cause:** Prior versions (v2.0.0) used a 680px centered white card on a gray background with `box-shadow`.

**Fix (v2.1.0):** The HTML wrapper now uses a clean white background without card borders, shadows, or border-radius. Update the app to v2.1.0.

### Issue: Styles lost/modified in email

1. The app wraps all content in a clean HTML layout with inline styles
2. Avoid editing the HTML body in Power Automate (pass it through as-is)
3. Do NOT enable any "clean HTML" or "sanitize" options in Power Automate

### Issue: Large payload errors

Each email may include screenshots (~100-500KB base64 each). If hitting size limits:
1. Reduce screenshot resolution in app settings
2. Limit the number of inline images in the email template

---

## 9. Migration from v2.0.0 or v1.x

If you have an existing Power Automate flow:

1. Update the HTTP trigger schema to remove `screenshotName`/`screenshotContent`/`screenshotContentId`/`cidAttachments` fields (see Section 3)
2. In the "Send an email (V2)" action, keep **only one attachment** (Excel): `attachmentName` / `attachmentContent`
3. **Remove** Attachment 2 (screenshot) — images are now embedded in the HTML body
4. **Remove** any "Apply to each" loop over `cidAttachments` (no longer needed)
5. Ensure the `body` field is passed through without modification
6. Save and test with the app's test mode

No changes needed to the trigger URL — the same URL works across versions.
