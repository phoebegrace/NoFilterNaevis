import streamlit as st
from openai import AsyncOpenAI
import asyncio
import random
import difflib

# Instantiate the OpenAI async client
client = AsyncOpenAI(api_key=st.secrets["API_key"])

# Function to load CSS
def load_css():
    st.markdown(
        """
        <style>
        .stApp {
            background-color: #000000;
        }
        .main-title {
            text-align: center;
            color: #fff;
        }
        .sidebar .sidebar-content {
            background-color: #000000;
            color: white;
        }
        .css-1aumxhk {
            font-size: 20px;
        }
        .stButton > button {
            background-color: #2a555e;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .stButton > button:hover {
            background-color: #ffffff;
            color: #281633;
        }
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #000;
            color: white;
            text-align: center;
            padding: 10px 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Load the CSS
load_css()

# Banner image
st.image("naevis.jpg", use_column_width=True)

async def generate_question(difficulty, topic):
    # Use OpenAI API to generate a single question based on the difficulty and topic
    prompt = f"Create one {difficulty} quiz question about {topic}. Format the response as 'Question: <question> Hint: <hint> Answer: <answer>'."
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.choices[0].message.content.strip()
    return text

def extract_question_hint_answer(text):
    try:
        parts = text.split("Answer:")
        question_hint = parts[0].split("Hint:")
        question = question_hint[0].replace("Question:", "").strip()
        hint = question_hint[1].strip()
        answer = parts[1].strip()
        return question, hint, answer
    except ValueError:
        return text, "No hint available", "Unknown"

def is_answer_correct(user_answer, correct_answer):
    try:
        # Try to compare as numbers
        user_answer_num = float(user_answer)
        correct_answer_num = float(correct_answer)
        return abs(user_answer_num - correct_answer_num) < 1e-6  # Small tolerance for floating point comparison
    except ValueError:
        # Fall back to string comparison if not numeric
        return difflib.SequenceMatcher(None, user_answer.lower().strip(), correct_answer.lower().strip()).ratio() > 0.8

async def get_comment(correct):
    # Use OpenAI API to generate a humorous and sarcastic comment based on the correctness of the answer
    correctness = "correct" if correct else "incorrect"
    prompt = f"Generate a humorous and sarcastic Taglish comment for a {correctness} answer."
    response = await client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    comment = response.choices[0].message.content.strip()
    return comment

def main():
    st.markdown("<h1 class='main-title'>Naevis Asks</h1>", unsafe_allow_html=True)
    
    # Welcome message
    st.markdown("""
        ## Welcome to Naevis Asks!
        ### Your Ultimate Quiz Experience
        Hello! This is NaevisAsks! I’m Naevis, and I’m thrilled to welcome you here! I am here to challenge your knowledge and provide some fun. Whether you’re a devoted K-pop fan or a trivia lover, you’re in the right place. Select your favorite topic, choose a difficulty level, and let's dive into the quiz. Together, we'll explore fascinating facts and see how high you can score.
    """, unsafe_allow_html=True)   

    # Initialize score in session state
    if "score" not in st.session_state:
        st.session_state.score = 0
        
    # Initialize other necessary session state attributes
    if "question" not in st.session_state:
        st.session_state.question = ""
    if "hint" not in st.session_state:
        st.session_state.hint = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""
    if "checked" not in st.session_state:
        st.session_state.checked = False
    if "answer_correct" not in st.session_state:
        st.session_state.answer_correct = None
    if "previous_questions" not in st.session_state:
        st.session_state.previous_questions = set()
    if "comment" not in st.session_state:
        st.session_state.comment = ""

    # Score values based on difficulty level
    score_values = {"easy": 1, "medium": 2, "hard": 3}

    # Selection for topic
    topic = st.selectbox("Select a topic:", ["Trivia", "Math", "General Knowledge", "Earth Science", "K-POP", "Philippine History", "Riddles", "Philippine Knowledge", "K-Drama", "Philippine Entertainment"])
    
    # Selection for difficulty level
    difficulty = st.selectbox("Select the difficulty level:", ["easy", "medium", "hard"])

    def generate_new_question():
        with st.spinner('Generating question...'):
            while True:
                question_text = asyncio.run(generate_question(difficulty, topic))
                question, hint, answer = extract_question_hint_answer(question_text)
                if question not in st.session_state.previous_questions:
                    st.session_state.previous_questions.add(question)
                    st.session_state.question, st.session_state.hint, st.session_state.answer = question, hint, answer
                    break
            st.session_state.user_answer = ""  # Clear the previous answer
            st.session_state.checked = False  # Reset checked state
            st.session_state.answer_correct = None  # Reset answer correctness
            st.session_state.comment = ""  # Clear the previous comment
    
    # Generate a new question if button is clicked
    if st.button("Generate Question"):
        generate_new_question()
                
    # Display the current question
    if st.session_state.question:
        st.markdown(f"<h3>Question:</h3><p>{st.session_state.question}</p>", unsafe_allow_html=True)

        with st.form(key="submit_form"):
            user_answer = st.text_input("Your answer:", value=st.session_state.user_answer)
            submit_button = st.form_submit_button(label="Submit Answer")

            if submit_button:
                st.session_state.user_answer = user_answer  # Store the user's answer
                st.session_state.checked = True  # Mark as checked
                st.session_state.answer_correct = is_answer_correct(user_answer, st.session_state.answer)
                st.session_state.comment = asyncio.run(get_comment(st.session_state.answer_correct))
                if st.session_state.answer_correct:
                    st.success("Correct!")
                    st.session_state.score += score_values[difficulty]
                else:
                    st.error(f"Incorrect! The correct answer was: {st.session_state.answer}")

        # Show hint button
        if st.button("Show Hint"):
            st.info(f"Hint: {st.session_state.hint}")

    # Display Naevis' comment
    if st.session_state.checked and st.session_state.comment:
        st.markdown(f"**Naevis:** {st.session_state.comment}")

    # "I am correct" button
    if st.session_state.checked and not st.session_state.answer_correct:
        if st.button("I am Correct", key="i_am_correct"):
            st.success("You confirmed your answer as correct!")
            st.session_state.score += score_values[difficulty]

    # "Next Question" button
    if st.session_state.checked:
        if st.button("Next Question"):
            generate_new_question()
            st.experimental_rerun()  # Ensure the new question is displayed immediately

    # Display the current score
    st.markdown(f"<h3>Your current score is: {st.session_state.score}</h3>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>Phoebe Grace Juayong, BSCS - 3A</div>", unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
