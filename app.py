# app.py
import streamlit as st
import os
import time
import json
from dotenv import load_dotenv
from openai import OpenAI
import datetime
import random
import re

# Load environment variables from .env
load_dotenv()

# Custom CSS for ADHD-friendly design
st.markdown("""
<style>
    /* Base styles */
    .stTextArea textarea {font-size: 18px !important;}
    button {background: #4CAF50 !important; color: white !important;}
    
    /* Task styling */
    .task-header {
        font-size: 1.4rem;
        font-weight: bold;
        margin: 20px 0 15px 0;
        padding: 10px;
        border-bottom: 1px solid #eee;
    }
    
    /* Mode headers */
    .mode-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 15px 0 10px 0;
        color: #333;
    }
    
    /* Robotic mode items */
    .robotic-step {
        margin: 10px 0;
        padding-left: 20px;
    }
    
    /* Creative mode items */
    .creative-step {
        margin: 10px 0;
        padding-left: 20px;
    }
    
    /* Activation hack */
    .activation-hack {
        margin: 15px 0;
        padding: 10px;
        background-color: #f9f9f9;
        border-left: 3px solid #ffc107;
        font-style: italic;
    }
    
    /* Emphasis for key actions */
    .key-action {
        font-weight: bold;
        color: #0066cc;
    }
    
    /* Arrow styling */
    .arrow {
        color: #888;
        margin: 0 5px;
    }
    
    /* Checkbox styling */
    .stCheckbox {
        padding-left: 10px;
    }
    
    /* Task divider */
    .task-divider {
        margin: 30px 0;
        border-top: 1px solid #eee;
    }
    
    /* Log container */
    .log-container {
        background: #f0f0f0; 
        padding: 10px; 
        border-radius: 5px; 
        max-height: 300px; 
        overflow-y: auto; 
        font-family: monospace;
    }
    
    /* Debug sections */
    .prompt-display, .response-display {
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-family: monospace;
        font-size: 0.9rem;
    }
    .prompt-display {
        background: #e6f7ff;
        border-left: 4px solid #1890ff;
    }
    .response-display {
        background: #f6ffed;
        border-left: 4px solid #52c41a;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state for logs if it doesn't exist
if 'logs' not in st.session_state:
    st.session_state.logs = []

# Initialize session state for task states and expanded sections
if 'task_states' not in st.session_state:
    st.session_state.task_states = {}

if 'expanded_tasks' not in st.session_state:
    st.session_state.expanded_tasks = {}

# Add a session state to store the last successful response
if 'last_tasks' not in st.session_state:
    st.session_state.last_tasks = None

def log_entry(message, level="INFO"):
    """Add a timestamped log entry to the session state"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    entry = f"[{timestamp}] [{level}] {message}"
    st.session_state.logs.append(entry)
    return entry

def display_logs():
    """Display all logs in the session state"""
    if st.session_state.logs:
        log_html = "<div class='log-container'>"
        for entry in st.session_state.logs:
            log_html += f"<div class='log-entry'>{entry}</div><br>"
        log_html += "</div>"
        st.markdown(log_html, unsafe_allow_html=True)

# Example JSON output for the LLM
JSON_EXAMPLE = """
{
    "Buy Spectacles (Don't Know What Frames Are Nice)": {
        "Robotic Mode (For Paralysis):": [
            "1. **Spend 2 mins**: Google "best glasses for [face shape]" → Screenshot 1-2 frames you like.",
            "2. **Tomorrow**: Show screenshots to a friend (text: "Which of these suits me?").",
            "3. **Next day**: Book 10-min try-on at nearest optician (link to book)."
        ],
        "Creative Mode": [
            "🎥 Watch "How to Pick Glasses" by [YouTube stylist] (8 mins).",
            "📱 *Use "Warby Parker Virtual Try-On" app (play with 5 frames).*",
            "💡 Ask ChatGPT: "I like [description]. Suggest frame styles?"",
            "⚡ Activation Hack: "Just find 1 frame you hate—elimination is progress!""
        ]
    },
    "Task: "Do Personal Projects (Too Many Ideas)": {
        "Robotic Mode (For Overwhelm):": [
            "1. Dump all ideas into app → AI auto-tags:",
            "2. Set a timer for 25 mins: Focus on the first task without distractions.",
            "3. After 25 mins, take a 5-min break to stretch or grab water."
        ],
        "Creative Mode": [
            "🗂️ Use a 'Kanban board' (like Trello) to visualize tasks and progress.",
            "📱 Try the 'Forest' app to stay focused while working and grow a virtual tree.",
            "⚡ Activation Hack: 'Start with the easiest task for just 5 mins—momentum builds!'"
        ]
    }
}
"""

def display_random_tip():
    """Display a random ADHD productivity tip"""
    tips = [
        "⚡ Starting is the hardest part - aim for just 2 minutes",
        "🧩 Break big tasks into tiny, ridiculously small steps",
        "🔄 Body doubling: work alongside someone (even virtually)",
        "⏰ Time block with timers - work in short bursts",
        "🎯 The 1-3-5 rule: 1 big task, 3 medium tasks, 5 small tasks",
        "🧠 External brain: write EVERYTHING down",
        "🎮 Gamify your tasks - add points, rewards or challenges",
        "👁️ Make it visible - sticky notes, visual reminders",
        "🌈 Create a dopamine menu - list quick activities that make you happy",
        "🚀 Two-Minute Rule – If it takes less than 2 minutes, do it immediately.",
        "📌 Anchor Task – Start your day with one small, grounding task to build momentum.",
        "🎧 Soundtrack Your Focus – Use instrumental music or white noise to minimize distractions.",
        "🏷️ Label Your Time – Give each block of time a fun or silly name to make it more engaging.",
        "🤹 Task Batching – Group similar small tasks together to reduce switching costs.",
        "📱 App Jail – Use focus apps to block distracting sites during work sprints.",
        "🧳 The Suitcase Method – Visualize packing tasks into 'suitcases' (time blocks) to make them feel more manageable.",
        "🛑 Set a 'Worry Time' – If random thoughts pop up, jot them down and save them for a designated 10-minute worry break.",
        "🔄 The 5-4-3-2-1 Trick – Count down from 5 and then just start—no overthinking.",
        "🏆 Completion Celebrations – Reward yourself immediately after finishing a task (even if it's just a happy dance).",
    ]
    return random.choice(tips)

def get_ai_response(user_input, mode):
    """Get task breakdown from OpenAI with mode-specific prompting"""
    log_entry(f"Starting AI request process for input: '{user_input}' with mode: {mode}")
    
    system_prompt = """
    You are a productivity coach specializing in ADHD/autism-friendly task breakdowns. Your output must EXACTLY follow these formatting rules:

    1. Main Task Headers:
       - Number each task (1., 2., etc.)
       - Use this exact format: "Task: "[Task name]" ([brief description])"
       - Example: "Task: "Buy Spectacles (Don't Know What Frames Are Nice)"

    2. Robotic Mode Section:
       - Use header: "Robotic Mode (For [specific purpose]):"
       - Create EXACTLY 3 numbered steps (1., 2., 3.)
       - Bold key action words
       - Use arrows (→) between main actions
       - Include time-based cues like "Tomorrow:"
       - For complex steps, use indented bullet points with colored circles (🟢, 🟡, 🔴)

    3. Creative Mode Section:
       - Use header: "Creative Mode (Explore Options):" or similar descriptive subtitle
       - Use bullet points (•) with emoji prefixes
       - Italicize app names
       - Use quotes for suggested phrases or searches

    4. Activation Hack Section:
       - Always include this as a separate section at the end of each task
       - Format: "Activation Hack: "[short, quotation-marked suggestion]"
       - Keep very brief and low-effort

    5. Visual Hierarchy:
       - Use consistent spacing between sections
       - Keep lines short (under 70 characters)
       - Use emojis as visual anchors
       - Bold critical information

    Your output will be shown to ADHD users who need clear visual organization and minimal cognitive load.
    """
    
    # Example response format - exactly matching the expected output
    example_response = """
    {
        "Task: \\"Buy Spectacles (Don't Know What Frames Are Nice)\\"": {
            "Robotic Mode (For Paralysis)": [
                "1. Spend 2 mins: Google \\"best glasses for [face shape]\\" → Screenshot 1-2 frames you like.",
                "2. Tomorrow: Show screenshots to a friend (text: \\"Which of these suits me?\\").",
                "3. Next day: Book 10-min try-on at nearest optician (link to book)."
            ],
            "Creative Mode (Explore Options)": [
                "🎥 Watch \\"How to Pick Glasses\\" by [YouTube stylist] (8 mins).",
                "📱 *Use \\"Warby Parker Virtual Try-On\\" app* (play with 5 frames).",
                "💡 Ask ChatGPT: \\"I like [description]. Suggest frame styles?\\""
            ],
            "Activation Hack": "\\"Just find 1 frame you hate—elimination is progress!\\""
        },
        "Task: \\"Do Personal Projects (Too Many Ideas)\\"": {
            "Robotic Mode (For Overwhelm)": [
                "1. Dump all ideas into app → AI auto-tags:",
                "2. Pick 1 \\"easy win\\" → \\"Code a button that changes color on click (1-hour project).\\"",
                "3. Set timer for 25 mins and start."
            ],
            "Creative Mode (Explore + Narrow Down)": [
                "🤖 \\"AI, rank my projects by: fun, learning, portfolio value.\\"",
                "🎲 Roll a dice: Let fate pick your next project!",
                "🎯 Block out exactly 30 minutes for project exploration."
            ],
            "Activation Hack": "\\"Work on any project for 5 mins—no commitment.\\""
        }
    }
    """
    
    # Create few-shot learning prompt with example
    user_prompt = f"""Mode: {mode}
    Input: {user_input}

    Here's an example of what I'm looking for:

    'Break down this task for ADHD users: "Plan healthy meals for the week".
    Use Robotic Mode (numbered steps) and Creative Mode (bulleted options).
    Include 1 activation hack with bold label.'

    Example Response:

    
    Please respond with a JSON object in the following format:
    ```json
    {example_response}
    ```

    Your response should only contain the JSON object, nothing else. The JSON object should include both Robotic Mode and Creative Mode options regardless of which mode was selected.

    Output:"""
    
    # Display prompts
    # st.markdown("<div class='prompt-display'><strong>System Prompt:</strong><br>" + system_prompt.replace('\n', '<br>') + "</div>", unsafe_allow_html=True)
    # st.markdown("<div class='prompt-display'><strong>User Prompt:</strong><br>" + user_prompt.replace('\n', '<br>') + "</div>", unsafe_allow_html=True)
    
    # # Display example section
    # st.markdown("<div class='example-display'><strong>Using JSON Format:</strong><br>The AI will respond with structured data for better task organization.</div>", unsafe_allow_html=True)
    
    log_entry("Prompts prepared and displayed with JSON example")
    
    # Create animation placeholder
    animation_placeholder = st.empty()
    dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    try:
        log_entry("Initializing OpenAI client")
        # Use OpenAI's updated API format
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        log_entry("OpenAI client initialized successfully")
        
        # Log model and parameters
        log_entry(f"Using model: gpt-4o-mini", "CONFIG")
        log_entry(f"Temperature: {0.3 if mode == '🤖 Robotic' else 0.7}", "CONFIG")
        log_entry(f"Max tokens: 2000", "CONFIG")
        
        # Show initial animation frame
        start_time = time.time()
        animation_placeholder.markdown(f"<h3>⠋ Generating response... (0.0s)</h3>", unsafe_allow_html=True)
        
        # Make the API call
        log_entry("Sending request to OpenAI API", "API")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3 if mode == "🤖 Robotic" else 0.7,
            max_tokens=2000,
            response_format={"type": "json_object"}  # Request JSON format
        )
        
        # Clear the animation
        animation_placeholder.empty()
        
        elapsed = time.time() - start_time
        log_entry(f"Response received in {elapsed:.2f} seconds", "SUCCESS")
        
        # Log and extract the content
        content = response.choices[0].message.content
        log_entry(f"Raw response: {content[:100]}...", "DATA")
        
        # # Display raw response in collapsible section
        # st.markdown("<details><summary>View Raw JSON Response</summary><pre>" + 
        #            content.replace("<", "&lt;").replace(">", "&gt;") + "</pre></details>", 
        #            unsafe_allow_html=True)
        
        return content
        
    except Exception as e:
        animation_placeholder.empty()
        error_msg = str(e)
        log_entry(f"API Error: {error_msg}", "ERROR")
        st.error(f"API Error: {error_msg}")
        return f"I couldn't process your request due to an error. Please try again. Error: {error_msg}"

def task_callback(task_key):
    """Toggle task expanded state"""
    st.session_state.expanded_tasks[task_key] = not st.session_state.expanded_tasks.get(task_key, False)
    log_entry(f"Task {task_key} expanded state toggled to {st.session_state.expanded_tasks[task_key]}")

def checkbox_callback(step_key):
    """Toggle checkbox state without causing a full rerun"""
    current_value = st.session_state.task_states.get(step_key, False) #step_key is the key of the checkbox, False is the default value if the key is not found
    st.session_state.task_states[step_key] = not current_value #toggle the state of the checkbox
    log_entry(f"Checkbox {step_key} toggled to {st.session_state.task_states[step_key]}")

def parse_json_response(response_text):
    """Parse the JSON response from the API"""
    try:
        tasks = json.loads(response_text) #loads the response text into a dictionary
        log_entry(f"Successfully parsed JSON with {len(tasks)} tasks")
        return tasks
    except json.JSONDecodeError as e:
        log_entry(f"Error parsing JSON: {str(e)}", "ERROR")
        
        # Try to extract JSON if it's surrounded by backticks or other text
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            try:
                tasks = json.loads(json_match.group(1))
                log_entry("Successfully extracted and parsed JSON from code block")
                log_entry(f"Parsed JSON: {tasks}")
                return tasks
            except json.JSONDecodeError:
                log_entry("Error parsing JSON from code block", "ERROR")
        
        st.error("The AI response wasn't in valid JSON format. Please try again.")
        return None

# App Layout
st.title("🧠 Brain Dump → Steps")
st.markdown("#### ADHD/Autism-friendly task breakdown with activation energy hacks")

# Random tip
st.info(display_random_tip())

# Add a section for logs with expander
# with st.expander("View Logs & Debug Info", expanded=False):
#     display_logs()
#     if st.button("Clear Logs"):
#         st.session_state.logs = []

mode = st.radio("Mode:", ["🤖 Robotic: Hyper-specific, minimal decision making, lowest activation energy", "🎨 Creative: Multiple approaches with visual aids and technology options"], horizontal=True)
log_entry(f"Mode selected: {mode}")

# Explain modes
# if mode == "🤖 Robotic":
#     st.caption("Robotic Mode: Hyper-specific, minimal decision making, lowest activation energy")
# else:
#     st.caption("Creative Mode: Multiple approaches with visual aids and technology options")

user_input = st.text_area("Brain Dump here:", 
                         placeholder="e.g., 'it's a good day but wah stress leh need to do taxes, call mom, fix bike, learn piano...I feel overwhelmed'")

# Update the main button handler:
if st.button("✨ Process My Chaos"):
    log_entry("Process button clicked")
    if user_input:
        log_entry(f"Processing input: '{user_input}'")
        response = get_ai_response(user_input, mode)
        
        # Parse the JSON response
        tasks = parse_json_response(response)
        log_entry(f"Tasks: {tasks}")
        
        if tasks:
            # Save the tasks in session state
            st.session_state.last_tasks = tasks
    else:
        log_entry("No input provided", "WARNING")
        st.warning("Please enter some tasks!")

# Display tasks section (outside the button click handler)
if st.session_state.last_tasks:
    st.subheader("Your Recommended AI-Generated Action Plan:")
    tasks = st.session_state.last_tasks
    
    # Display tasks
    for task_index, (task_name, modes) in enumerate(tasks.items(), 1):
        log_entry(f"Displaying task: {task_name}")
        log_entry(f"Modes: {modes}")
        log_entry(f"Task index: {task_index}")
        
        # Clean up task name - remove "Task:" prefix and quotes
        clean_task_name = task_name
        if clean_task_name.startswith('Task:'):
            clean_task_name = clean_task_name[5:].strip()
        # Remove surrounding quotes if present
        clean_task_name = re.sub(r'^"(.*)"$', r'\1', clean_task_name)
        
        # Task header with number prefix
        st.markdown(f"<div class='task-header'>{task_index}. {clean_task_name}</div>", unsafe_allow_html=True)
        
        # Robotic Mode
        if any(key.startswith("Robotic Mode") for key in modes.keys()):
            # Find the key that starts with "Robotic Mode"
            robotic_key = next((key for key in modes.keys() if key.startswith("Robotic Mode")), None) #next returns the first item in the list that satisfies the condition
            if robotic_key:
                # Clean up the key - remove any trailing colons
                display_key = robotic_key.rstrip(':')
                st.markdown(f"<div class='mode-header'>{display_key}:</div>", unsafe_allow_html=True)
                
                # Display each step with proper styling
                for i, step in enumerate(modes[robotic_key]):
                    log_entry(f"Step: {step}")
                    step_key = f"task_{task_index}_robotic_{i}" 
                    # Initialize checkbox state if it doesn't exist
                    if step_key not in st.session_state.task_states:
                        st.session_state.task_states[step_key] = False
                    
                    # Check if step already starts with a number (like "1.")
                    if re.match(r'^\d+\.', step.strip()):
                        # Already has a number, use as is
                        display_step = step
                    else:
                        # Add the number (i+1 to start from 1 instead of 0)
                        display_step = f"{i+1}. {step}"
                    
                    # Display checkbox with proper numbering
                    st.checkbox(
                        display_step,
                        key=step_key,
                        value=st.session_state.task_states.get(step_key, False)
                    )
        
        # Creative Mode
        if any(key.startswith("Creative Mode") for key in modes.keys()):
            # Find the key that starts with "Creative Mode"
            creative_key = next((key for key in modes.keys() if key.startswith("Creative Mode")), None)
            if creative_key:
                # Clean up the key - remove any trailing colons
                display_key = creative_key.rstrip(':')
                st.markdown(f"<div class='mode-header'>{display_key}:</div>", unsafe_allow_html=True)
                
                # Display each step with proper styling (as bullets)
                for i, step in enumerate(modes[creative_key]):
                    step_key = f"task_{task_index}_creative_{i}"
                    
                    # Initialize checkbox state if it doesn't exist
                    if step_key not in st.session_state.task_states:
                        st.session_state.task_states[step_key] = False
                    
                    # Display checkbox with no callback to avoid reruns
                    st.checkbox(
                        step,
                        key=step_key,
                        value=st.session_state.task_states.get(step_key, False)
                    )
        
        # Activation Hack (rendered differently - as a callout)
        if "Activation Hack" in modes:
            hack_text = modes["Activation Hack"].replace('⚡ **Activation Hack:**', '')
            st.markdown(f"<div class='mode-header'>Activation Hack:</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='activation-hack'>{hack_text}</div>", unsafe_allow_html=True)
        
        # Task divider
        if task_index < len(tasks):
            st.markdown("<hr class='task-divider'>", unsafe_allow_html=True)