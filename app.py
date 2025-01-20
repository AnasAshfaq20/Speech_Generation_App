import openai
import streamlit as st
from PyPDF2 import PdfReader

# Set OpenAI API Key
api_key = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI(api_key=api_key)

# Function to generate or enhance a speech
def process_speech(speech_text, enhance=False):
    if enhance:
        instruction = f"""
        You are an assistant tasked with enhancing a speech. The provided speech is below:
        
        {speech_text}
        
        Please improve the structure, language, and flow. Make it more engaging and impactful while preserving the original message.
        """
    else:
        instruction = f"""
        You are an assistant tasked with creating a speech based entirely on the user-provided questions and answers below. Every detail provided in the QA must be used as context to shape the speech. The speech should be well-structured, engaging, and tailored to the event.

        Questions and Answers:
        {speech_text}

        Language: Generate the speech in detail in the language mentioned in the QA.
        """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": instruction}],
        stream=True
    )
    return response

# Function to extract text from uploaded PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Initialize Streamlit UI
st.title("🎤 Speech Generator & Enhancer")

# Tab-based UI for options
tab1, tab2 = st.tabs(["Generate New Speech", "Enhance Existing Speech"])

# Tab 1: Generate New Speech
with tab1:
    with st.form("speech_form"):
        st.header("Fill Out the Speech Questionnaire")

        # Collect user inputs
        st.session_state.responses = {
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
            "language": st.text_input("11. Language for the Speech", placeholder="e.g., English, Spanish, Urdu"),
        }

        # Submit Button
        submitted = st.form_submit_button("Generate Speech")

    # Check if all inputs are filled after button click
    if submitted:
        is_all_filled = all(value != "" for value in st.session_state.responses.values())
        
        if is_all_filled:
            # Convert responses to QA format
            qa_text = "\n".join([f"Q: {key.replace('_', ' ').title()} A: {value}" for key, value in st.session_state.responses.items() if value])

            # Generate speech
            if qa_text:
                with st.spinner("Generating your personalized speech..."):
                    speech_placeholder = st.empty()
                    full_response = ""
                    for part in process_speech(qa_text):
                        if hasattr(part.choices[0].delta, "content") and part.choices[0].delta.content:
                            full_response += part.choices[0].delta.content
                            speech_placeholder.markdown(f"**Your Speech (Generating...):**\n\n{full_response}▌")
                    speech_placeholder.markdown(f"**Your Final Speech:**\n\n{full_response}")
                
                    # Display the generated speech
                    st.session_state.conversation = [{"role": "user", "content": full_response}]
                    st.write("**Your Speech:**")
                    st.markdown(full_response)

                    # User input for further editing after speech generation
                    user_input = st.text_area("Provide further improvements or edits to the speech:")

                    # Button to regenerate speech based on user input
                    if st.button("Regenerate Speech with Improvements"):
                        if user_input:
                            # Add the user's feedback to the conversation history
                            st.session_state.conversation.append({"role": "user", "content": user_input})

                            # Process the updated speech with new input
                            with st.spinner("Re-generating speech based on your input..."):
                                updated_speech = ""
                                for part in process_speech("\n".join([msg['content'] for msg in st.session_state.conversation]), enhance=True):
                                    if hasattr(part.choices[0].delta, "content") and part.choices[0].delta.content:
                                        updated_speech += part.choices[0].delta.content

                                # Display the updated speech
                                st.write("**Updated Speech:**")
                                st.markdown(updated_speech)
        else:
            st.warning("Please fill in all fields to generate the speech.")

# Tab 2: Enhance Existing Speech
with tab2:
    st.header("Upload Your Speech (PDF)")
    uploaded_file = st.file_uploader("Upload a PDF file containing your speech:", type=["pdf"])

    if uploaded_file is not None:
        # Extract text from the uploaded PDF
        speech_text = extract_text_from_pdf(uploaded_file)
        st.write("**Original Speech:**")
        st.write(speech_text)

        # Enhance Speech Button
        if st.button("Enhance Speech"):
            with st.spinner("Enhancing your speech..."):
                speech_placeholder = st.empty()
                full_response = ""
                for part in process_speech(speech_text, enhance=True):
                    if hasattr(part.choices[0].delta, "content") and part.choices[0].delta.content:
                        full_response += part.choices[0].delta.content
                        speech_placeholder.markdown(f"**Enhanced Speech (Generating...):**\n\n{full_response}▌")
                speech_placeholder.markdown(f"**Your Enhanced Speech:**\n\n{full_response}")

                # Allow user to provide input for further edits after enhancement
                st.session_state.conversation = [{"role": "user", "content": full_response}]
                user_input = st.text_area("Provide further improvements or edits to the speech:")

                # Button to regenerate speech based on user input
                if st.button("Regenerate Enhanced Speech with Improvements"):
                    if user_input:
                        # Add the user's feedback to the conversation history
                        st.session_state.conversation.append({"role": "user", "content": user_input})

                        # Process the updated speech with new input
                        with st.spinner("Re-generating enhanced speech based on your input..."):
                            updated_speech = ""
                            for part in process_speech("\n".join([msg['content'] for msg in st.session_state.conversation]), enhance=True):
                                if hasattr(part.choices[0].delta, "content") and part.choices[0].delta.content:
                                    updated_speech += part.choices[0].delta.content

                            # Display the updated enhanced speech
                            st.write("**Updated Enhanced Speech:**")
                            st.markdown(updated_speech)
