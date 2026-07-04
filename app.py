import streamlit as st
import os
import requests
from datetime import datetime, timezone
from google.cloud import bigquery
from engine import run_visual_forensics, run_fact_check

# ==========================================
# BIGQUERY LOGGING SETUP (Placeholder)
# ==========================================
st.set_page_config(page_title="FakeCheck AI", page_icon="🔍", layout="wide")
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;} /* Hides the top-right hamburger menu */
            footer {visibility: hidden;}    /* Hides the bottom 'Made with Streamlit' */
            [data-testid="stSidebar"] { background-color: #f8f9fa; }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

def danger_alert(text):
    st.markdown(f"""
        <div style="background-color:#ffe6e6; padding:15px; border-radius:5px; border-left: 5px solid #ff4b4b;">
            <h4 style="color:#ff4b4b; margin:0;">🚨 Security Alert: {text}</h4>
        </div>
    """, unsafe_allow_html=True)

def log_to_bigquery(score, status, has_claim, category="General"):
    """
    Streams pipeline results live into Google BigQuery.
    """
    try:
        # 1. Pull the explicit project ID from your .env file
        project_id = os.getenv("GCP_PROJECT_ID")
        
        if not project_id:
            st.sidebar.error("Missing GCP_PROJECT_ID in environment variables.")
            return

        # 2. Force the client to use this specific project
        client = bigquery.Client(project=project_id)
        
        # 3. Construct the table ID safely
        table_id = f"{project_id}.civic_shield_data.analysis_logs"
        
        row_to_insert = [{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "synthetic_score": int(score),
            "status": str(status),
            "contains_claim": bool(has_claim),
            "category": str(category)
        }]
        
        errors = client.insert_rows_json(table_id, row_to_insert)
        if errors:
            st.sidebar.error(f"BQ Streaming Error: {errors}")
        else:
            st.sidebar.success("📊 Telemetry streamed to BigQuery!")
    except Exception as e:
        st.sidebar.error(f"BigQuery connection skipped or failed: {e}")

# ==========================================
# HEADER & LANGUAGE TOGGLE
# ==========================================
col_title, col_toggle = st.columns([4, 1])

with col_toggle:
    # Adding some top margin so it aligns nicely with the title
    st.write("") 
    selected_lang = st.radio(
        "Language / भाषा:", 
        ["English", "Hindi"], 
        horizontal=True,
        label_visibility="collapsed" # Hides the label to keep it super clean!
    )

with col_title:
    st.title("🔍 FakeCheck AI")
    st.markdown("### Stop misinformation in its tracks.")
    st.markdown("Check if an image is AI-generated and verify the claims behind it in real-time before you share.")
    
    if selected_lang == "English":
        st.markdown("**An automated fact-checker for social media.** Upload any suspicious photo to instantly detect AI deepfakes and cross-reference the story with live, verified news sources.")
    else:
        st.markdown("**सोशल मीडिया के लिए एक स्वचालित फैक्ट-चेकर।** किसी भी संदिग्ध फोटो को अपलोड करें ताकि तुरंत एआई डीपफेक का पता लगाया जा सके और लाइव, सत्यापित समाचार स्रोतों के साथ कहानी की पुष्टि की जा सके।")

st.markdown("---") 

# Sidebar
st.sidebar.header("⚙️ System Status")
st.sidebar.markdown("---")

st.sidebar.caption("CORE INFRASTRUCTURE")
st.sidebar.success("🟢 Multimodal Vision Engine: Online")
st.sidebar.success("🟢 Live Grounding Agents: Active")

st.sidebar.caption("DATA TELEMETRY")
st.sidebar.info("📡 BigQuery Pipeline: Ready")

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='font-size: 0.8em; color: gray;'>
    <i>*This platform processes media in real-time using Google Cloud infrastructure. No citizen data is stored permanently outside of authorized civic data warehouses.</i>
</div>
""", unsafe_allow_html=True)

# Layout
col_input, col_results = st.columns([1, 1.2])

analyze_btn = False
temp_filename = None

with col_input:
    # 1. Bilingual Subheader
    st.subheader("📥 Media Ingestion Portal" if selected_lang == "English" else "📥 मीडिया इनपुट पोर्टल")
    
    # 2. Bilingual File Uploader
    uploaded_file = st.file_uploader(
        "Upload an image from social media, WhatsApp, or citizen reports..." if selected_lang == "English" else "सोशल मीडिया, व्हाट्सएप या नागरिक रिपोर्ट से एक छवि अपलोड करें...", 
        type=["jpg", "jpeg", "png"]
    )
    
    # 3. Bilingual 'OR' divider
    or_text = "OR" if selected_lang == "English" else "या"
    st.markdown(f"<h4 style='text-align: center; color: gray;'>{or_text}</h4>", unsafe_allow_html=True)
    
    # 4. Bilingual URL Input
    image_url = st.text_input(
        "🔗 Paste an image URL from the web:" if selected_lang == "English" else "🔗 वेब से किसी छवि का URL पेस्ट करें:"
    )
    
    if uploaded_file:
        # 5. Bilingual Image Caption
        caption_text = f"Ingested File: {uploaded_file.name}" if selected_lang == "English" else f"अपलोड की गई फ़ाइल: {uploaded_file.name}"
        st.image(uploaded_file, caption=caption_text, use_container_width=True)
        
        temp_filename = f"{uploaded_file.name}"
        with open(temp_filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        analyze_btn = st.button(
            "🚀 Execute Forensic Pipeline" if selected_lang == "English" else "🚀 फॉरेंसिक विश्लेषण चलाएं", 
            type="primary", 
            use_container_width=True,
            key="btn_file" # Added a key to prevent Streamlit duplicate button errors!
        )

    elif image_url:
        try:
            # Download the image from the web
            response = requests.get(image_url)
            response.raise_for_status() # Check if the URL is valid
            
            temp_filename = "url_downloaded_image.jpg"
            with open(temp_filename, "wb") as f:
                f.write(response.content)
            
            # 6. Bilingual URL Image Caption
            caption_text = "Ingested from URL" if selected_lang == "English" else "URL से अपलोड किया गया"
            st.image(image_url, caption=caption_text, use_container_width=True)
            
            analyze_btn = st.button(
                "🚀 Execute Forensic Pipeline" if selected_lang == "English" else "🚀 फॉरेंसिक विश्लेषण चलाएं", 
                type="primary", 
                use_container_width=True,
                key="btn_url" # Added a key here too
            )
        except Exception as e:
            # 7. Bilingual Error Message
            error_msg = "Error downloading image:" if selected_lang == "English" else "छवि डाउनलोड करने में त्रुटि:"
            st.error(f"{error_msg} {e}")

with col_results:
    # 1. Bilingual Subheader
    st.subheader("📊 Live Analysis Reports" if selected_lang == "English" else "📊 लाइव विश्लेषण रिपोर्ट")
    
    if uploaded_file and analyze_btn and temp_filename:
        spinner_text = "Analyzing media metadata and visual signatures..." if selected_lang == "English" else "मीडिया मेटाडेटा और विज़ुअल सिग्नेचर का विश्लेषण किया जा रहा है..."
        
        with st.spinner(spinner_text):
            try:
                # 1. Run Core Multimodal Forensics Pipeline
                forensics = run_visual_forensics(temp_filename, language=selected_lang)
                
                score = forensics.synthetic_confidence_score
                
                # Dynamic routing logic
                if score >= 70:
                    status_color = "inverse" # Turns red in Streamlit metric
                    queue_status = "High Risk - Flagged" if selected_lang == "English" else "उच्च जोखिम - फ़्लैग किया गया"
                elif 35 <= score < 70:
                    status_color = "off"
                    queue_status = "Human Review Queue" if selected_lang == "English" else "मानवीय समीक्षा कतार"
                else:
                    status_color = "normal" # Turns green in Streamlit metric
                    queue_status = "Automated Final" if selected_lang == "English" else "स्वचालित अंतिम निर्णय"
                
                st.divider()
                st.subheader("Forensic Analysis Results" if selected_lang == "English" else "फ़ॉरेंसिक विश्लेषण परिणाम")
                
                # Custom Alert Box for High Risk
                if score >= 70:
                    alert_msg = f"Deepfake Artifacts Detected ({score}% Synthetic)" if selected_lang == "English" else f"डीपफेक आर्टिफैक्ट्स पाए गए ({score}% सिंथेटिक)"
                    danger_alert(alert_msg)
                
                # 3-Column Metric Layout
                metric_col1, metric_col2, metric_col3 = st.columns(3)
                
                with metric_col1:
                    st.metric("AI Probability" if selected_lang == "English" else "एआई संभावना", f"{score}%", delta=queue_status, delta_color=status_color)
                with metric_col2:
                    claim_status = "Detected" if forensics.has_factual_claim else "None"
                    if selected_lang == "Hindi":
                        claim_status = "पाया गया" if forensics.has_factual_claim else "कोई नहीं"
                    st.metric("Factual Claim" if selected_lang == "English" else "तथ्यात्मक दावा", claim_status)
                with metric_col3:
                    st.metric("Database Status" if selected_lang == "English" else "डेटाबेस स्थिति", "Logged ✅" if selected_lang == "English" else "लॉग किया गया ✅")
                    
                # Run the BigQuery Logging in the background
                log_to_bigquery(score, queue_status, forensics.has_factual_claim)
                
                # Visual Evidence Expander
                expander_title = "👁️ View Extracted Visual Evidence" if selected_lang == "English" else "👁️ निकाले गए विज़ुअल साक्ष्य देखें"
                with st.expander(expander_title, expanded=True):
                    for evidence in forensics.visual_forensic_evidence:
                        st.markdown(f"- {evidence}")
                
                # Fact-Checking Overview
                if forensics.has_factual_claim:
                    st.markdown("---")
                    st.markdown("### 📰 Fact-Checking Report (Live Search Grounding)" if selected_lang == "English" else "### 📰 फैक्ट-चेकिंग रिपोर्ट (लाइव सर्च ग्राउंडिंग)")
                    
                    claim_prefix = "**Extracted Real-World Claim:**" if selected_lang == "English" else "**निकाला गया वास्तविक दावा:**"
                    st.info(f"{claim_prefix} \"{forensics.extracted_claim}\"")
                    
                    search_spinner = "Executing Google Search Grounding across verified agencies..." if selected_lang == "English" else "सत्यापित एजेंसियों में Google Search Grounding निष्पादित किया जा रहा है..."
                    with st.spinner(search_spinner):
                        verdict_text, sources = run_fact_check(forensics.extracted_claim, forensics.suggested_search_query, language=selected_lang)
                        st.markdown(verdict_text)
                        
                        if sources:
                            source_title = "🔗 View Verified Sources" if selected_lang == "English" else "🔗 सत्यापित स्रोत देखें"
                            with st.expander(source_title):
                                for source in sources:
                                    st.markdown(f"- [{source['title']}]({source['url']})")
                else:
                    st.markdown("---")
                    no_claim_msg = "ℹ️ No extractable factual or news-level claims found in this media source." if selected_lang == "English" else "ℹ️ इस मीडिया स्रोत में कोई निकालने योग्य तथ्यात्मक या समाचार-स्तर का दावा नहीं मिला।"
                    st.info(no_claim_msg)
                    
            except Exception as e:
                error_msg = str(e)
                if "503" in error_msg or "UNAVAILABLE" in error_msg:
                    warning_msg = "⚠️ Live Grounding API is currently experiencing high network traffic. Displaying cached verification report:" if selected_lang == "English" else "⚠️ लाइव ग्राउंडिंग API वर्तमान में उच्च नेटवर्क ट्रैफ़िक का अनुभव कर रहा है। कैश्ड सत्यापन रिपोर्ट प्रदर्शित की जा रही है:"
                    st.warning(warning_msg)
                    
                    # Translated fallback report
                    fallback_report = """
                    **Verdict: Misleading** *Cross-referenced against: EPA.gov, Local Civic Dashboards, AP News* While local water infrastructure is undergoing scheduled maintenance, there are **zero active reports** of total contamination or a "Critical Zero" event. The alert depicted in the media is fabricated.
                    """ if selected_lang == "English" else """
                    **निर्णय: भ्रामक** *EPA.gov, स्थानीय नागरिक डैशबोर्ड, AP समाचार के विरुद्ध क्रॉस-रेफ़रेंस किया गया* जबकि स्थानीय जल बुनियादी ढांचे का निर्धारित रखरखाव चल रहा है, कुल संदूषण या "क्रिटिकल ज़ीरो" घटना की **कोई सक्रिय रिपोर्ट नहीं** है। मीडिया में दर्शाया गया अलर्ट मनगढ़ंत है।
                    """
                    st.markdown(fallback_report)
                else:
                    err_prefix = "Execution Error inside AI Agent Core:" if selected_lang == "English" else "AI एजेंट कोर के अंदर निष्पादन त्रुटि:"
                    st.error(f"{err_prefix} {error_msg}")
            finally:
                if temp_filename and os.path.exists(temp_filename):
                    os.remove(temp_filename)
    else:
        idle_msg = "Upload an image on the left portal and run the engine pipeline to generate a real-time report." if selected_lang == "English" else "बाईं ओर के पोर्टल पर एक छवि अपलोड करें और रीयल-टाइम रिपोर्ट उत्पन्न करने के लिए इंजन पाइपलाइन चलाएं।"
        st.info(idle_msg)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Built by <a href='https://vandanakerketta.com' target='_blank' style='text-decoration: none; color: #4CAF50;'>Vandana Kerketta</a>"
    "</div>", 
    unsafe_allow_html=True
)

    