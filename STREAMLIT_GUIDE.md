# Streamlit App - Quick Start Guide

## 🚀 Running the App

The Streamlit app is now running! You should see it open in your browser automatically, or you can access it at:

**http://localhost:8501**

## 📋 Features Available

### 1. **Home - Create Creative** (Main Feature)
- Upload packshot image (required)
- Upload background and logo (optional)
- Enter headline, price, and claim text
- Select formats (1:1, 4:5, 9:16)
- Generate creatives with compliance validation
- Download generated creatives

### 2. **Preview Layout**
- Quick preview of your creative before generating
- See how your layout will look
- Test different formats

### 3. **Validate Creative**
- Upload an existing creative
- Check compliance and risk level
- See extracted text and issues

### 4. **About**
- Information about the app and features

## 🎯 How to Use

1. **Upload Images:**
   - Packshot: Required (product image)
   - Background: Optional
   - Logo: Optional

2. **Enter Text:**
   - Headline: Main text
   - Price: e.g., "£9.99"
   - Claim: e.g., "Save 20% Today!"

3. **Select Formats:**
   - Check the formats you want (1:1, 4:5, 9:16)

4. **Generate:**
   - Click "Generate Creatives"
   - Wait 30-60 seconds for processing
   - View results and compliance data
   - Download your creatives

## ⚠️ Important Notes

- Processing takes time (30-60 seconds) - be patient!
- Make sure you have a packshot image uploaded
- All outputs are automatically compressed to < 500 KB
- Compliance validation shows risk levels (LOW/MEDIUM/HIGH)

## 🛑 Stopping the App

To stop the Streamlit app:
- Press `Ctrl+C` in the terminal
- Or close the terminal window

## 🔄 Restarting

To restart the app:
```bash
streamlit run streamlit_app.py
```

Enjoy testing your creative builder! 🎨

