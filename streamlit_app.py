"""
Streamlit Frontend for TESCORA.AI
AI-Assisted Tesco-Compliant Creative Builder
"""
import streamlit as st
from PIL import Image
import io
from pathlib import Path
import json
from datetime import datetime

from backend.api import (
    process_creative_api,
    preview_layout_api,
    get_formats_api,
    validate_creative_api
)

# Page configuration
st.set_page_config(
    page_title="TESCORA.AI - Creative Builder",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #0065FF;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #333;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        margin: 1rem 0;
    }
    .creative-card {
        border: 2px solid #ddd;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #f9f9f9;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'processed_results' not in st.session_state:
    st.session_state.processed_results = None
if 'preview_image' not in st.session_state:
    st.session_state.preview_image = None
if 'preview_format' not in st.session_state:
    st.session_state.preview_format = None

# Header
st.markdown('<h1 class="main-header">🎨 TESCORA.AI</h1>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; font-size: 1.2rem; color: #666;">AI-Assisted Tesco-Compliant Creative Builder</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📋 Navigation")
    page = st.radio(
        "Choose a page",
        ["🏠 Home - Create Creative", "👁️ Preview Layout", "✅ Validate Creative", "ℹ️ About"]
    )

# Home Page - Create Creative
if page == "🏠 Home - Create Creative":
    st.markdown('<h2 class="sub-header">Create Your Creative</h2>', unsafe_allow_html=True)
    
    # Get available formats
    try:
        formats = get_formats_api()
    except Exception as e:
        st.error(f"Error loading formats: {e}")
        formats = ["1:1", "4:5", "9:16"]
    
    # File uploads
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📸 Upload Images")
        packshot_file = st.file_uploader(
            "Product Packshot (Required)",
            type=['jpg', 'jpeg', 'png'],
            help="Upload your product packshot image"
        )
        
        background_file = st.file_uploader(
            "Background Image (Optional)",
            type=['jpg', 'jpeg', 'png'],
            help="Upload a background image for your creative"
        )
        
        logo_file = st.file_uploader(
            "Logo (Optional)",
            type=['jpg', 'jpeg', 'png'],
            help="Upload your brand logo"
        )
    
    with col2:
        st.subheader("✍️ Text Inputs")
        headline = st.text_input(
            "Headline",
            placeholder="Enter your headline text",
            help="Main headline for your creative"
        )
        
        price = st.text_input(
            "Price",
            placeholder="e.g., £9.99",
            help="Product price to display"
        )
        
        claim = st.text_input(
            "Claim",
            placeholder="e.g., Save 20% Today!",
            help="Promotional claim or offer"
        )
    
    # Format selection
    st.subheader("📐 Creative Formats")
    format_cols = st.columns(len(formats))
    selected_formats = []
    
    for i, fmt in enumerate(formats):
        with format_cols[i]:
            if st.checkbox(f"{fmt}", value=True, key=f"format_{fmt}"):
                selected_formats.append(fmt)
    
    # Format descriptions
    format_descriptions = {
        "1:1": "Instagram Feed (1080x1080)",
        "4:5": "Facebook Feed (1080x1350)",
        "9:16": "Instagram Reels/Stories (1080x1920)"
    }
    
    st.info("💡 **Formats Selected:** " + ", ".join([f"{f} - {format_descriptions.get(f, '')}" for f in selected_formats]) if selected_formats else "No formats selected")
    
    # Compliance option
    run_compliance = st.checkbox("Run Compliance Validation", value=True, help="Validate creative for compliance issues")
    
    # Process button
    if st.button("🚀 Generate Creatives", type="primary", use_container_width=True):
        if not packshot_file:
            st.error("❌ Please upload a packshot image to continue")
        elif not selected_formats:
            st.error("❌ Please select at least one format")
        else:
            with st.spinner("🔄 Processing your creative... This may take 30-60 seconds."):
                try:
                    # Save uploaded files temporarily
                    upload_dir = Path("uploads")
                    upload_dir.mkdir(exist_ok=True)
                    
                    packshot_path = upload_dir / f"packshot_{packshot_file.name}"
                    with open(packshot_path, "wb") as f:
                        f.write(packshot_file.getbuffer())
                    
                    background_path = None
                    if background_file:
                        background_path = upload_dir / f"background_{background_file.name}"
                        with open(background_path, "wb") as f:
                            f.write(background_file.getbuffer())
                    
                    logo_path = None
                    if logo_file:
                        logo_path = upload_dir / f"logo_{logo_file.name}"
                        with open(logo_path, "wb") as f:
                            f.write(logo_file.getbuffer())
                    
                    # Process creative
                    results = process_creative_api(
                        packshot_path=str(packshot_path),
                        background_path=str(background_path) if background_path else None,
                        logo_path=str(logo_path) if logo_path else None,
                        headline=headline if headline else None,
                        price=price if price else None,
                        claim=claim if claim else None,
                        formats=selected_formats,
                        run_compliance=run_compliance
                    )
                    
                    st.session_state.processed_results = results
                    
                    if results.get('success'):
                        st.success("✅ Creative generated successfully!")
                    else:
                        st.error(f"❌ Error: {results.get('errors', ['Unknown error'])}")
                
                except Exception as e:
                    st.error(f"❌ Error processing creative: {str(e)}")
                    st.exception(e)
    
    # Display results
    if st.session_state.processed_results and st.session_state.processed_results.get('success'):
        results = st.session_state.processed_results
        
        st.markdown("---")
        st.markdown('<h2 class="sub-header">📦 Generated Creatives</h2>', unsafe_allow_html=True)
        
        # Display exports
        exports = results.get('exports', {})
        for format_name, export_data in exports.items():
            if export_data.get('success'):
                with st.expander(f"📐 {format_name} - {format_descriptions.get(format_name, '')}", expanded=True):
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Display image
                        image_path = export_data.get('path')
                        if image_path and Path(image_path).exists():
                            img = Image.open(image_path)
                            st.image(img, caption=f"Creative {format_name}", use_container_width=True)
                    
                    with col2:
                        st.write("**Details:**")
                        st.write(f"📏 Dimensions: {export_data.get('dimensions', 'N/A')}")
                        st.write(f"💾 Size: {export_data.get('size_kb', 0):.2f} KB")
                        st.write(f"✅ Size Valid: {'Yes' if export_data.get('size_valid') else 'No'}")
                        
                        # Download button
                        if image_path and Path(image_path).exists():
                            with open(image_path, "rb") as f:
                                st.download_button(
                                    label="⬇️ Download",
                                    data=f.read(),
                                    file_name=f"creative_{format_name.replace(':', '_')}.jpg",
                                    mime="image/jpeg",
                                    use_container_width=True
                                )
                    
                    # Compliance results
                    if results.get('compliance') and format_name in results['compliance']:
                        compliance = results['compliance'][format_name]
                        
                        st.markdown("---")
                        st.markdown("**🔍 Compliance Results:**")
                        
                        # Risk level badge
                        risk_level = compliance.get('risk_level', 'UNKNOWN')
                        risk_colors = {
                            'LOW': '🟢',
                            'MEDIUM': '🟡',
                            'HIGH': '🔴'
                        }
                        risk_emoji = risk_colors.get(risk_level, '⚪')
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"{risk_emoji} **Risk Level:** {risk_level}")
                        with col2:
                            is_compliant = compliance.get('is_compliant', False)
                            st.write(f"{'✅' if is_compliant else '❌'} **Compliant:** {'Yes' if is_compliant else 'No'}")
                        
                        # Issues
                        issues = compliance.get('issues', [])
                        if issues:
                            st.warning(f"⚠️ **{len(issues)} Issue(s) Found:**")
                            for issue in issues:
                                st.write(f"- **{issue.get('type', 'Unknown')}:** {issue.get('message', '')} (Risk: {issue.get('risk', 'UNKNOWN')})")
                        else:
                            st.success("✅ No compliance issues found!")
                        
                        # Warnings
                        warnings = compliance.get('warnings', [])
                        if warnings:
                            st.info(f"ℹ️ **{len(warnings)} Warning(s):**")
                            for warning in warnings:
                                st.write(f"- {warning.get('message', '')}")

# Preview Page
elif page == "👁️ Preview Layout":
    st.markdown('<h2 class="sub-header">Preview Your Layout</h2>', unsafe_allow_html=True)
    
    try:
        formats = get_formats_api()
    except Exception as e:
        formats = ["1:1", "4:5", "9:16"]
    
    # Format selection
    selected_format = st.selectbox("Select Format", formats)
    
    # File uploads
    col1, col2 = st.columns(2)
    
    with col1:
        packshot_file = st.file_uploader(
            "Product Packshot (Required)",
            type=['jpg', 'jpeg', 'png'],
            key="preview_packshot"
        )
        
        background_file = st.file_uploader(
            "Background Image (Optional)",
            type=['jpg', 'jpeg', 'png'],
            key="preview_background"
        )
        
        logo_file = st.file_uploader(
            "Logo (Optional)",
            type=['jpg', 'jpeg', 'png'],
            key="preview_logo"
        )
    
    with col2:
        headline = st.text_input("Headline", key="preview_headline")
        price = st.text_input("Price", key="preview_price")
        claim = st.text_input("Claim", key="preview_claim")
    
    if st.button("👁️ Generate Preview", type="primary", use_container_width=True):
        if not packshot_file:
            st.error("❌ Please upload a packshot image")
        else:
            with st.spinner("🔄 Generating preview..."):
                try:
                    # Save files
                    upload_dir = Path("uploads")
                    upload_dir.mkdir(exist_ok=True)
                    
                    packshot_path = upload_dir / f"preview_packshot_{packshot_file.name}"
                    with open(packshot_path, "wb") as f:
                        f.write(packshot_file.getbuffer())
                    
                    background_path = None
                    if background_file:
                        background_path = upload_dir / f"preview_bg_{background_file.name}"
                        with open(background_path, "wb") as f:
                            f.write(background_file.getbuffer())
                    
                    logo_path = None
                    if logo_file:
                        logo_path = upload_dir / f"preview_logo_{logo_file.name}"
                        with open(logo_path, "wb") as f:
                            f.write(logo_file.getbuffer())
                    
                    # Generate preview
                    preview_image = preview_layout_api(
                        format_name=selected_format,
                        packshot_path=str(packshot_path),
                        background_path=str(background_path) if background_path else None,
                        logo_path=str(logo_path) if logo_path else None,
                        headline=headline if headline else None,
                        price=price if price else None,
                        claim=claim if claim else None
                    )
                    
                    st.session_state.preview_image = preview_image
                    st.session_state.preview_format = selected_format
                    
                    st.success("✅ Preview generated!")
                
                except Exception as e:
                    st.error(f"❌ Error generating preview: {str(e)}")
                    st.exception(e)
    
    # Display preview
    if st.session_state.preview_image:
        st.markdown("---")
        st.markdown(f"<h3>Preview - {st.session_state.preview_format}</h3>", unsafe_allow_html=True)
        st.image(st.session_state.preview_image, use_container_width=True)
        
        # Download preview
        buffer = io.BytesIO()
        st.session_state.preview_image.save(buffer, format='PNG')
        st.download_button(
            label="⬇️ Download Preview",
            data=buffer.getvalue(),
            file_name=f"preview_{st.session_state.preview_format.replace(':', '_')}.png",
            mime="image/png",
            use_container_width=True
        )

# Validate Page
elif page == "✅ Validate Creative":
    st.markdown('<h2 class="sub-header">Validate Existing Creative</h2>', unsafe_allow_html=True)
    
    try:
        formats = get_formats_api()
    except Exception as e:
        formats = ["1:1", "4:5", "9:16"]
    
    creative_file = st.file_uploader(
        "Upload Creative to Validate",
        type=['jpg', 'jpeg', 'png'],
        help="Upload a creative image to check for compliance"
    )
    
    format_name = st.selectbox("Select Format", formats)
    
    if st.button("✅ Validate Creative", type="primary", use_container_width=True):
        if not creative_file:
            st.error("❌ Please upload a creative image")
        else:
            with st.spinner("🔄 Validating creative..."):
                try:
                    # Save file
                    upload_dir = Path("uploads")
                    upload_dir.mkdir(exist_ok=True)
                    
                    creative_path = upload_dir / f"validate_{creative_file.name}"
                    with open(creative_path, "wb") as f:
                        f.write(creative_file.getbuffer())
                    
                    # Validate
                    results = validate_creative_api(
                        creative_path=str(creative_path),
                        format_name=format_name
                    )
                    
                    # Display results
                    st.markdown("---")
                    st.markdown("**🔍 Validation Results:**")
                    
                    # Display image
                    img = Image.open(creative_path)
                    st.image(img, caption="Creative to Validate", use_container_width=True)
                    
                    # Risk level
                    risk_level = results.get('risk_level', 'UNKNOWN')
                    risk_colors = {
                        'LOW': '🟢',
                        'MEDIUM': '🟡',
                        'HIGH': '🔴'
                    }
                    risk_emoji = risk_colors.get(risk_level, '⚪')
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"{risk_emoji} **Risk Level:** {risk_level}")
                    with col2:
                        is_compliant = results.get('is_compliant', False)
                        st.write(f"{'✅' if is_compliant else '❌'} **Compliant:** {'Yes' if is_compliant else 'No'}")
                    
                    # Issues
                    issues = results.get('issues', [])
                    if issues:
                        st.warning(f"⚠️ **{len(issues)} Issue(s) Found:**")
                        for issue in issues:
                            st.write(f"- **{issue.get('type', 'Unknown')}:** {issue.get('message', '')} (Risk: {issue.get('risk', 'UNKNOWN')})")
                    else:
                        st.success("✅ No compliance issues found!")
                    
                    # Warnings
                    warnings = results.get('warnings', [])
                    if warnings:
                        st.info(f"ℹ️ **{len(warnings)} Warning(s):**")
                        for warning in warnings:
                            st.write(f"- {warning.get('message', '')}")
                    
                    # Extracted text
                    extracted = results.get('extracted_text', {})
                    if extracted:
                        with st.expander("📝 Extracted Text"):
                            st.write(f"**Full Text:** {extracted.get('full_text', 'N/A')}")
                            if extracted.get('prices'):
                                st.write(f"**Prices:** {[p.get('text') for p in extracted['prices']]}")
                            if extracted.get('claims'):
                                st.write(f"**Claims:** {extracted['claims']}")
                
                except Exception as e:
                    st.error(f"❌ Error validating creative: {str(e)}")
                    st.exception(e)

# About Page
else:
    st.markdown('<h2 class="sub-header">About TESCORA.AI</h2>', unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎨 AI-Assisted Tesco-Compliant Creative Builder
    
    **TESCORA.AI** helps advertisers quickly generate professional, guideline-aware, 
    multi-format retail media creatives with minimal manual effort.
    
    #### ✨ Features
    
    - **🤖 AI Background Removal**: Automatically remove backgrounds from product packshots
    - **📐 Multi-Format Generation**: Create creatives in 1:1, 4:5, and 9:16 formats
    - **✅ Compliance Validation**: Automated checks for risky claims and guideline violations
    - **👁️ Live Preview**: See your creative before generating
    - **📝 OCR Text Extraction**: Extract and validate text from images
    - **💾 Auto Compression**: All outputs under 500 KB
    
    #### 📐 Supported Formats
    
    - **1:1** (1080x1080) - Instagram Feed
    - **4:5** (1080x1350) - Facebook Feed  
    - **9:16** (1080x1920) - Instagram Reels/Stories
    
    #### 🔍 Compliance Checks
    
    - Safe zone validation
    - Contrast ratio checks (WCAG AA standard)
    - Text legibility verification
    - Claim risk assessment
    - Price validation
    
    #### 🚀 How to Use
    
    1. **Upload Assets**: Upload your packshot (required), background, and logo (optional)
    2. **Enter Text**: Add headline, price, and claim text
    3. **Select Formats**: Choose which formats to generate
    4. **Generate**: Click "Generate Creatives" and wait for processing
    5. **Review**: Check compliance results and download your creatives
    
    #### ⚠️ Important Notes
    
    - This is a **prototype** for hackathon demonstration
    - Processing may take 30-60 seconds
    - All images are automatically compressed to meet size requirements
    - Compliance validation provides risk assessment, not absolute enforcement
    
    ---
    
    **Built for Tesco Retail Media InnovAItion Jam**
    """)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #666;'>TESCORA.AI - AI-Assisted Creative Builder | Built for Tesco Hackathon</p>",
    unsafe_allow_html=True
)

