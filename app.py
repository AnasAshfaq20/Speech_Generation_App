from openai import OpenAI
import streamlit as st
from PyPDF2 import PdfReader

# Set OpenAI API Key
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

# Function to generate or enhance a speech with streaming
def process_speech(speech_text, enhance=False):
    instruction = (
        f"You are an assistant tasked with {'enhancing' if enhance else 'creating'} a speech."
        f"\nSpeech Content:\n{speech_text}\n"
        "Improve the structure, language, and flow to make it engaging and impactful."
        if enhance
        else f"""You are an assistant tasked with creating a speech based entirely on the user-provided questions and answers below. Every detail provided in the QA must be used as context to shape the speech. The speech should be well-structured, engaging, and tailored to the event.

        Questions and Answers:
        {speech_text}

        Language: Generate the speech in detail in the language mentioned in the QA."""
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": instruction}],
        temperature=0.5,
        stream=True,  # Enable streaming
    )

    # Collect the streamed response
    full_response = ""
    for part in response:
        if hasattr(part.choices[0].delta, "content") and part.choices[0].delta.content:
            full_response += part.choices[0].delta.content
            yield part.choices[0].delta.content  # Yield each part as it comes

# Function to extract text from uploaded PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Streamlit UI
st.title("🎤 Speech Generator & Enhancer")

# Initialize session state for speech data
if 'generated_speech' not in st.session_state:
    st.session_state.generated_speech = ""

# Tab-based UI
tab1, tab2 = st.tabs(["Generate New Speech", "Enhance Existing Speech"])

# Tab 1: Generate New Speech
with tab1:
    with st.form("speech_form"):
        st.header("Fill Out the Speech Questionnaire")
        # Collect user inputs
        responses = {
            "who_are_you": st.text_input("1. Who Are You?", placeholder="Best Man, Maid of Honor, etc."),
            "relationship_to_couple": st.text_input("2. Your Relationship to the Couple", placeholder="Groom's Brother, Bride's Friend, etc."),
            "names": st.text_input("3. Names/Nicknames (Bride, Groom, etc.)", placeholder="John (groom), Emma (bride)"),
            "speech_length": st.text_input("4. Desired Speech Length", placeholder="e.g., 5 minutes"),
            "tone": st.selectbox("5. Tone of the Speech", ["Funny", "Heartwarming", "Romantic", "Formal"]),
            "funny_anecdote": st.text_area("6. Funny Anecdote", placeholder="Share a humorous story about the couple."),
            "qualities_bride": st.text_area("7. Qualities of the Bride", placeholder="Her kindness, intelligence, etc."),
            "qualities_groom": st.text_area("8. Qualities of the Groom", placeholder="His loyalty, sense of humor, etc."),
            "heartwarming_memory": st.text_area("9. Heartwarming Memory", placeholder="A special trip, meaningful conversation, etc."),
            "theme_message": st.text_area("10. Message or Theme", placeholder="Love, friendship, family, etc."),
            "cultural_references": st.text_area("11. Include any specific cultural or religious references", placeholder="No specific references."),
            "inside_jokes": st.text_area("12. Any inside jokes or personal references", placeholder="John's obsession with pineapple pizza."),
            "end_with_toast": st.text_area("13. End the speech with a toast?", placeholder="Yes, please suggest a cheerful toast."),
            "avoid_topics": st.text_area("14. Any topics or subjects to avoid?", placeholder="Avoid mentioning past relationships."),
            "additional_info": st.text_area("15. Anything else to include?", placeholder="Additional details for the speech."),
            "language": st.text_input("16. Language for the Speech", placeholder="e.g., English, Spanish, Urdu"),
        }

        submitted = st.form_submit_button("Generate Speech")

if submitted:
    if all(value.strip() for value in responses.values()):
        qa_text = "\n".join([f"Q: {key.replace('_', ' ').title()} A: {value}" for key, value in responses.items()])
        with st.spinner("Generating your speech..."):
            speech_placeholder = st.empty()
            full_response = ""
            for part in process_speech(qa_text):
                full_response += part
                speech_placeholder.markdown(f"**Your Speech (Generating...):**\n\n{full_response}▌")
            st.session_state.generated_speech = full_response
    else:
        st.warning("Please fill out all fields.")

if st.session_state.generated_speech:
    user_input = st.text_area("Provide further improvements for the speech:", key="improvements")
    if st.button("Regenerate Speech with Improvements"):
        with st.spinner("Regenerating speech based on your input..."):
            speech_placeholder = st.empty()
            improved_speech = ""
            for part in process_speech(f"{st.session_state.generated_speech}\n\nImprovements:\n{user_input}", enhance=True):
                improved_speech += part
                speech_placeholder.markdown(f"**Your Updated Speech (Generating...):**\n\n{improved_speech}▌")
            st.session_state.generated_speech = improved_speech
        
# Initialize session state for enhanced speech
if 'enhanced_speech' not in st.session_state:
    st.session_state.enhanced_speech = ""

# Tab 2: Enhance Existing Speech
with tab2:
    st.header("Upload Your Speech (PDF)")
    uploaded_file = st.file_uploader("Upload a PDF file containing your speech:", type=["pdf"])

    if uploaded_file is not None:
        # Extract text from the uploaded PDF
        speech_text = extract_text_from_pdf(uploaded_file)
        st.write("### Extracted Speech Text")
        st.write(speech_text)

        if st.button("Enhance Speech"):
            with st.spinner("Enhancing your speech..."):
                speech_placeholder = st.empty()
                enhanced_speech = ""
                for part in process_speech(speech_text, enhance=True):
                    enhanced_speech += part
                    speech_placeholder.markdown(f"**Your Enhanced Speech (Generating...):**\n\n{enhanced_speech}▌")
                st.session_state.enhanced_speech = enhanced_speech

        if st.session_state.enhanced_speech:
            user_input = st.text_area("Provide further improvements for the enhanced speech:", key="enhance_improvements")
            if st.button("Regenerate Enhanced Speech"):
                with st.spinner("Regenerating enhanced speech based on your input..."):
                    speech_placeholder = st.empty()
                    further_enhanced_speech = ""
                    for part in process_speech(f"{st.session_state.enhanced_speech}\n\nImprovements:\n{user_input}", enhance=True):
                        further_enhanced_speech += part
                        speech_placeholder.markdown(f"**Your Further Enhanced Speech (Generating...):**\n\n{further_enhanced_speech}▌")
                    st.session_state.enhanced_speech = further_enhanced_speech
