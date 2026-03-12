# Power Automate Flow Construction Guide

> **Version:** 2.0.0
> **App:** Formación Evaluation Splitter
> **Last Updated:** 2026-03-10

---

## Overview

This document provides a complete guide for building the Power Automate flow that handles email sending for the Formación Evaluation Splitter app. The v2.0.0 flow supports:

- **Rich HTML email body** with full inline style preservation
- **CID-based inline images** (screenshots, logos, editor images)
- **Multiple attachments** per email (Excel file + inline images)
- **Table-based HTML layout** for maximum email client compatibility

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
│  │  Attachments: triggerBody()?['attachments']              │    │
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
            "description": "HTML email body (full HTML document with inline styles)"
        },
        "isHtml": {
            "type": "boolean",
            "description": "Always true for this app"
        },
        "attachmentName": {
            "type": "string",
            "description": "Primary attachment filename (legacy, for backward compatibility)"
        },
        "attachmentContent": {
            "type": "string",
            "description": "Primary attachment base64 content (legacy)"
        },
        "attachments": {
            "type": "array",
            "description": "Array of all attachments including CID inline images",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Filename (e.g., file.xlsx, screenshot.png)"
                    },
                    "content": {
                        "type": "string",
                        "description": "Base64-encoded file content"
                    },
                    "contentType": {
                        "type": "string",
                        "description": "MIME type (e.g., image/png, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet)"
                    },
                    "contentId": {
                        "type": "string",
                        "description": "Content-ID for CID inline images (optional, only for inline images)"
                    }
                }
            }
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

### 4.2 Attachments Configuration (CRITICAL for v2.0.0)

The `attachments` array in the payload contains ALL attachments — both the main Excel file and CID-referenced inline images.

**Option A: Using the `attachments` array directly (Recommended)**

In the "Send an email (V2)" action's advanced options:

1. Click **"Show advanced options"**
2. Find **"Attachments"**
3. Switch to **"Enter entire array"** mode
4. Use this expression:

```
@{triggerBody()?['attachments']}
```

**Option B: Apply to each (if Option A doesn't work)**

If your connector doesn't support direct array input:

1. Add **"Apply to each"** loop over `@{triggerBody()?['attachments']}`
2. Inside the loop, use the "Send an email (V2)" action outside the loop
3. For each attachment in the loop, add it to a variable array first

### 4.3 Handling CID Inline Images

CID (Content-ID) images are a standard mechanism for embedding images in HTML emails:

1. The image is sent as an attachment with a `contentId` field
2. The HTML body references it with `src="cid:<contentId>"`
3. The email client displays the image inline in the body

**Example:**
- Attachment: `{ "name": "screenshot.png", "content": "...", "contentType": "image/png", "contentId": "screenshot_excel" }`
- HTML: `<img src="cid:screenshot_excel" alt="Captura">`

Most email clients (Outlook, Gmail, Apple Mail) support CID images correctly.

---

## 5. Payload Examples

### 5.1 Full Payload (v2.0.0)

```json
{
  "to": "tutor@example.com",
  "cc": "manager@example.com;hr@example.com",
  "subject": "Evaluación Formación — Juan Berral",
  "body": "<!DOCTYPE html><html><head><meta charset='UTF-8'>...</head><body><table width='100%'>...<img src='cid:screenshot_excel'>...</table></body></html>",
  "isHtml": true,
  "attachmentName": "Juan_Berral_evaluaciones.xlsx",
  "attachmentContent": "UEsDBBQAAAAI...(base64 Excel)",
  "attachments": [
    {
      "name": "Juan_Berral_evaluaciones.xlsx",
      "content": "UEsDBBQAAAAI...(base64 Excel)",
      "contentType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    },
    {
      "name": "screenshot.png",
      "content": "iVBORw0KGgo...(base64 PNG)",
      "contentType": "image/png",
      "contentId": "screenshot_excel"
    },
    {
      "name": "inline_img_1.png",
      "content": "iVBORw0KGgo...(base64 PNG)",
      "contentType": "image/png",
      "contentId": "inline_img_1"
    }
  ]
}
```

### 5.2 Attachment Types

| Type | Purpose | Has `contentId`? | Appears in body? |
|------|---------|:---:|:---:|
| Excel (.xlsx) | Main file attachment | No | No — appears as downloadable attachment |
| Screenshot (.png) | Excel data screenshot | Yes (`screenshot_excel`) | Yes — via `<img src="cid:screenshot_excel">` |
| Inline Image (.png/.jpg) | Images from email editor | Yes (`inline_img_N`) | Yes — via `<img src="cid:inline_img_N">` |

---

## 6. HTML Body Structure

The email body sent by v2.0.0 is a complete HTML document with:

1. **Full HTML document** with `<!DOCTYPE html>`, `<html>`, `<head>`, `<body>` tags
2. **Table-based layout** for maximum email client compatibility
3. **All styles inline** (no `<style>` blocks, no CSS classes)
4. **CID image references** instead of base64 data-URIs

```html
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f4f4f4;">
  <table width="100%" cellpadding="0" cellspacing="0" style="...">
    <tr>
      <td align="center">
        <table width="680" cellpadding="0" cellspacing="0" style="background-color:#ffffff;...">
          <!-- Header row -->
          <tr>
            <td style="background-color:#2563eb; color:#ffffff; padding:20px 30px;">
              <h1>Evaluación Formación</h1>
            </td>
          </tr>
          <!-- Content row -->
          <tr>
            <td style="padding:30px; font-family:Calibri,Arial,sans-serif;">
              <!-- Editor content with inline styles goes here -->
              <!-- CID images referenced as: <img src="cid:screenshot_excel"> -->
            </td>
          </tr>
          <!-- Footer row -->
          <tr>
            <td style="...">
              <p>Email generado automáticamente</p>
            </td>
          </tr>
        </table>
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
| CID images | ✅ | ✅ | ✅ | ✅ |
| Custom fonts | ✅ | ✅ | ⚠️ | ✅ |
| Background colors | ✅ | ✅ | ✅ | ✅ |

### Why CID instead of Base64 Data URIs?

| Approach | Pros | Cons |
|----------|------|------|
| **Base64 data-URI** | Self-contained, no extra attachments | Blocked by many email clients (Outlook, Gmail) |
| **CID attachment** | Universally supported, standard mechanism | Requires attachments array |
| **External URL** | Small payload | Requires hosting, may be blocked by firewalls |

The app uses **CID attachments** as the optimal balance between compatibility and reliability.

---

## 8. Troubleshooting

### Issue: Images not displaying in email

1. Verify the `contentId` in attachments matches the `cid:` reference in HTML
2. Check that Power Automate is passing the `attachments` array correctly
3. Test with Outlook Desktop first (best CID support)

### Issue: Styles lost/modified in email

1. The app wraps all content in a table-based HTML layout with inline styles
2. Avoid editing the HTML body in Power Automate (pass it through as-is)
3. Do NOT enable any "clean HTML" or "sanitize" options in Power Automate

### Issue: Large payload errors

Each email may include screenshots (~100-500KB base64 each). If hitting size limits:
1. Reduce screenshot resolution in app settings
2. Limit the number of inline images in the email template

### Issue: Legacy flow (v1.x) compatibility

The payload includes both:
- Legacy fields: `attachmentName`, `attachmentContent` (single Excel file)
- New field: `attachments` array (all files including CID images)

A v1.x flow will still work for the Excel attachment but will not show inline images.

---

## 9. Migration from v1.x

If you have an existing v1.x Power Automate flow:

1. Update the HTTP trigger schema to include the `attachments` property (see Section 3)
2. In the "Send an email (V2)" action, change attachments from single file to array mode
3. Use `@{triggerBody()?['attachments']}` for the attachments field
4. Save and test with the app's test mode

No changes needed to the trigger URL — the same URL works for both v1.x and v2.0.0 payloads.
