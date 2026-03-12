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
            "description": "Excel attachment filename"
        },
        "attachmentContent": {
            "type": "string",
            "description": "Excel attachment base64-encoded content"
        },
        "cidAttachments": {
            "type": "array",
            "description": "CID inline images only (screenshots, editor images). Excel is NOT included here.",
            "items": {
                "type": "object",
                "properties": {
                    "Name": {
                        "type": "string",
                        "description": "Filename (e.g., screenshot.png)"
                    },
                    "ContentBytes": {
                        "type": "string",
                        "description": "Base64-encoded image content"
                    },
                    "ContentType": {
                        "type": "string",
                        "description": "MIME type (e.g., image/png)"
                    },
                    "ContentId": {
                        "type": "string",
                        "description": "Content-ID referenced in HTML as cid:<ContentId>"
                    },
                    "IsInline": {
                        "type": "boolean",
                        "description": "Always true for CID inline images"
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

The payload separates Excel and CID images into **two distinct fields** to avoid connector parsing issues:

| Field | Purpose | Flow configuration |
|-------|---------|-------------------|
| `attachmentName` + `attachmentContent` | Excel file (base64) | Individual attachment fields |
| `cidAttachments` | CID inline images only | "Apply to each" loop |

#### Step A: Excel attachment (individual fields — simple and reliable)

In the "Send an email (V2)" action's **Attachments** section, click **"Add new item"**:

| Attachment field | Expression |
|-----------------|------------|
| **Name** | `@{triggerBody()?['attachmentName']}` |
| **Content** | `@{triggerBody()?['attachmentContent']}` |
| **Content Type** | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

This uses the base64-encoded Excel content directly — the most reliable approach.

#### Step B: CID inline images (Apply to each loop)

Add an **"Apply to each"** action **before** the Send email action:

1. Loop over: `@triggerBody()?['cidAttachments']`
2. Inside the loop, use a **"Append to array variable"** action to build a `varCidAttachments` array
3. Value to append: the current item (expression: `@items('Apply_to_each')`)

Then in "Send an email (V2)", add more items to Attachments from `varCidAttachments`, or use a second "Enter entire array" mode for the CID images only:

```
@variables('varCidAttachments')
```

> **Note:** If your template has no screenshots, `cidAttachments` will be an empty array and the loop does nothing.

### 4.3 Handling CID Inline Images

CID (Content-ID) images are a standard mechanism for embedding images in HTML emails:

1. The image is sent as an attachment with `ContentId` and `IsInline: true`
2. The HTML body references it with `src="cid:<ContentId>"`
3. The email client displays the image inline in the body

**Example:**
- Attachment: `{ "Name": "screenshot.png", "ContentBytes": "...", "ContentType": "image/png", "ContentId": "screenshot_excel", "IsInline": true }`
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
  "body": "<!DOCTYPE html>...<img src='cid:screenshot_excel'>...</html>",
  "isHtml": true,
  "attachmentName": "Juan_Berral_evaluaciones.xlsx",
  "attachmentContent": "UEsDBBQAAAAI...(base64 Excel)",
  "cidAttachments": [
    {
      "Name": "screenshot.png",
      "ContentBytes": "iVBORw0KGgo...(base64 PNG)",
      "ContentType": "image/png",
      "ContentId": "screenshot_excel",
      "IsInline": true
    },
    {
      "Name": "inline_img_1.png",
      "ContentBytes": "iVBORw0KGgo...(base64 PNG)",
      "ContentType": "image/png",
      "ContentId": "inline_img_1",
      "IsInline": true
    }
  ]
}
```

### 5.2 Attachment Fields

| Field | Type | Contains | Flow field |
|-------|------|---------|------------|
| `attachmentName` | string | Excel filename | Attachments → Name |
| `attachmentContent` | string (base64) | Excel file bytes | Attachments → Content |
| `cidAttachments` | array | CID inline images only | Apply to each loop |

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

### Issue: Excel attachment cannot be opened ("formato no coincide con extensión")

**Cause:** The Excel content was not reaching the connector as actual file bytes.

**Fix (v2.0.0 architecture):** Excel attachment uses **individual fields**, NOT the array:
- Attachments → Name: `@{triggerBody()?['attachmentName']}`
- Attachments → Content: `@{triggerBody()?['attachmentContent']}`

`attachmentContent` is already base64-encoded by the app — the connector decodes it automatically.

---

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

1. Update the HTTP trigger schema to include the `cidAttachments` property (see Section 3)
2. In the "Send an email (V2)" action, keep Excel in individual attachment fields (`attachmentName` / `attachmentContent`)
3. Add an "Apply to each" loop over `@triggerBody()?['cidAttachments']` for inline images
4. Save and test with the app's test mode

No changes needed to the trigger URL — the same URL works for both v1.x and v2.0.0 payloads.
