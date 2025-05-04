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
    
    /* Additional CSS specifically for expander headers */
    .task-expander-header {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: #1e3a8a !important;
        padding: 10px !important;
    }
    
    
    /* Target additional Streamlit expander classes */
    div[data-testid="stExpander"] {
        border-left: 5px solid #4CAF50 !important;
        background-color: #f8f9fa !important;
        border-radius: 8px !important;
    }
    .st-emotion-cache-1h9usn1 p {
        font-size: 18px !important;
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
    """Add a timestamped log entry to the session state and console"""
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
        "🧩 Break big tasks into tiny, ridiculously small steps (from 'How to ADHD' by Jessica McCabe)",
        "🔄 Body doubling: work alongside someone (even virtually)",
        "⏰ Time block with timers - work in short bursts",
        "🎯 The 1-3-5 rule: 1 big task, 3 medium tasks, 5 small tasks",
        "🧠 External brain: write EVERYTHING down (from 'Driven to Distraction' by Dr. Hallowell)",
        "🎮 Gamify your tasks - add points, rewards or challenges (from Jane McGonigal's research)",
        "👁️ Make it visible - sticky notes, visual reminders",
        "🌈 Create a dopamine menu - list quick activities that make you happy",
        "🚀 Two-Minute Rule – If it takes less than 2 minutes, do it immediately (from 'Getting Things Done' by David Allen)",
        "📌 Anchor Task – Start your day with one small, grounding task to build momentum",
        "🎧 Soundtrack Your Focus – Use instrumental music or white noise to minimize distractions",
        "🏷️ Label Your Time – Give each block of time a fun or silly name to make it more engaging",
        "🤹 Task Batching – Group similar small tasks together to reduce switching costs",
        "📱 App Jail – Use focus apps to block distracting sites during work sprints",
        "🧳 The Suitcase Method – Visualize packing tasks into 'suitcases' (time blocks) to make them feel more manageable",
        "🛑 Set a 'Worry Time' – Schedule specific time to worry about things (from CBT techniques)",
        "🔄 The 5-4-3-2-1 Trick – Count down from 5 and then just start (from Mel Robbins' '5 Second Rule')",
        "🏆 Completion Celebrations – Reward yourself immediately after finishing a task (from BJ Fogg's Tiny Habits)",
        "💡 Use the 'Forest' app to stay focused while working and grow a virtual tree",
        "🎯 Use the 'Pomodoro Technique' to break work into 25-minute sprints (by Francesco Cirillo)",

    ]
    return random.choice(tips)

def display_adhd_affirmation():
    """Display a random affirmation message for ADHD individuals"""
    affirmations = [
        "Your brain isn't broken—it's just wired for a world that doesn't exist yet.",
        "That pile of unfinished projects? They're evidence of your boundless curiosity, not your failure.",
        "You notice what others miss, feel what others dismiss, and see connections invisible to many.",
        "The chaos you navigate daily would overwhelm those who judge you most harshly.",
        "Your \"too much\" energy is exactly what this world needs—never apologize for your spark.",
        "The path is harder for you, but the view is more beautiful through your eyes.",
        "For every task you forgot, remember how many brilliant thoughts have crossed your mind.",
        "Your struggle to fit into neurotypical spaces isn't weakness—it's like trying to run underwater.",
        "You're not alone—millions navigate this same invisible current against them every day.",
        "When executive function fails, remember: worth isn't measured by productivity.",
        "Your hyperfocus isn't a flaw—it's your superpower in disguise.",
        "The same brain that loses keys can solve problems others can't even see.",
        "Self-compassion isn't just nice—for you, it's necessary fuel for the journey.",
        "Behind every \"I can't believe I did that again\" is an \"I'm still here, still trying.\"",
        "Your resilience in a world not built for you is nothing short of remarkable.",
        "Time blindness means you live more fully in each moment—a gift and challenge both.",
        "You've developed strength through constant adaptation that most will never understand.",
        "Remember: medication, strategies, and support aren't crutches—they're glasses for your mind.",
        "Your different perspective isn't just valid—it's vital to human progress.",
        "You belong here, exactly as you are—wild, wonderful brain and all.",
        "Hey you, with the 37 browser tabs open and that sinking feeling you're forgetting something important—I see you.",
        "Remember how you rehearsed that 'quick phone call' for an hour, then forgot what you wanted to say anyway? Same.",
        "That shame spiral when someone says 'just make a schedule' like you haven't tried a hundred times? I know it well.",
        "The panic of realizing you've been scrolling for two hours when you sat down to 'quickly check something'—you're not alone in this.",
        "That pile of half-finished projects isn't evidence of failure—it's the battlefield where you fight your brain chemistry daily.",
        "I know how it feels when people mistake your time blindness for not caring, when actually you care too much.",
        "You're not crazy for needing noise to focus sometimes and silence other times. Your brain just has its own operating system.",
        "The exhaustion after a day of 'normal' interactions? That's real. Masking drains us in ways others can't see.",
        "Those moments when your thoughts race so fast you can't catch them all—I drop those balls too.",
        "I understand the grief of thinking 'what could I have accomplished if my brain worked differently?'",
        "When you apologize for being 'too much'—stop. The world needs your intensity and the connections only you can make.",
        "Those random bursts of motivation aren't character flaws—they're how our engines run. Use them when they come.",
        "Your messy desk, forgotten appointments, and impulsive decisions don't define your worth or intelligence.",
        "Remember how you solved that problem everyone else was stuck on? That's your divergent thinking at work.",
        "When you're beating yourself up for procrastinating again—pause. Our brains require different conditions to launch.",
        "The medicine, sticky notes, and phone alarms aren't signs of weakness—they're tools, like glasses for someone with blurry vision.",
        "You've survived every overwhelming day so far, creating workarounds the neurotypical world will never appreciate enough.",
        "On days when executive function is offline, remember: existing is enough. The dishes can wait.",
        "This lonely road feels less lonely when we walk it together, sharing our maps and shortcuts.",
        "Your beautifully chaotic, creative, struggling, resilient ADHD brain belongs in this world. And you're doing better than you think.",
    ]
    return random.choice(affirmations)

def get_emotional_validation(user_input):
    """Get an empathetic response that matches the user's emotional state"""
    try:
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
        
        # First detect the emotion type
        emotion_check = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an emotion detector. Categorize the emotional tone into one of these categories: 'negative' (stressed, sad, overwhelmed, frustrated), 'positive' (happy, excited, determined), or 'neutral' (no clear emotion)."},
                {"role": "user", "content": f"What type of emotion does this text convey? Is it netural, positive, or negative? Just use the words 'neutral', 'positive', or 'negative' to describe the emotion. '{user_input}'"}
            ],
            temperature=0.1,
            max_tokens=10
        )
        
        emotion_type = emotion_check.choices[0].message.content.strip().lower()
        log_entry(f"Emotion detected: {emotion_type}")
        
        # Skip validation only if neutral
        if "neutral" in emotion_type:
            log_entry("Neutral emotion detected, skipping validation")
            return None
            
        # Choose appropriate system prompt based on emotion type
        if "positive" in emotion_type:
            system_content = """You are an enthusiastic coach who specializes in supporting people with ADHD/autism.
            Provide a short, encouraging response (2-3 sentences) that:
            1. Acknowledges their positive energy or determination
            2. Amplifies their momentum
            3. Offers specific encouragement to keep going
            
            Keep your response energetic, authentic, and under 50 words. Be specific to their situation."""
        else:  # negative emotions
            system_content = """You are an empathetic coach who specializes in supporting people with ADHD/autism.
            Provide a short, validating response (2-3 sentences) that:
            1. Acknowledges their emotions and struggles
            2. Normalizes their experiences
            3. Offers gentle encouragement
            
            Keep your response warm, authentic, and under 50 words. Be specific to their situation."""
        
        # Get appropriate validation response
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": f"Respond to this statement with appropriate support: '{user_input}'"}
            ],
            temperature=0.88,
            max_tokens=555
        )
        return response.choices[0].message.content
            
    except Exception as e:
        log_entry(f"Error getting emotional validation: {str(e)}", "ERROR")
        return None

def get_ai_response(user_input, mode):
    """Get task breakdown from OpenAI with mode-specific prompting"""
    log_entry(f"Starting AI request process for input: '{user_input}' with mode: {mode}, granularity level: {st.session_state.granularity_level}")
    
    # Add granularity level instructions to the system prompt
    granularity_instructions = ""
    if st.session_state.granularity_level == 1:
        granularity_instructions = """
        Task Granularity: LEVEL 1 (MINIMAL)
        - Create 1-4 steps per task
        - Focus on broad action summaries (e.g., "**Research options** → Compare 3 brands")
        - Include only essential tools/time estimates
        - Perfect for quick planning or high executive function days
        """
    elif st.session_state.granularity_level == 2:
        granularity_instructions = """
        Task Granularity: LEVEL 2 (MODERATE)
        - Create 4-8 steps per task
        - Each step = 1 concrete action + context
        - Balance between overview and details
        - Provide specific actions with some context
        - Good for most days and situations
        - Format: "**Action summary**: Specifics → Next step (time)"
        - Example: "**Compare frames**: Use Warby Parker app → Save 2 favorites (10 mins)"
        """
    else:  # Level 3
        granularity_instructions = """
        Task Granularity: LEVEL 3 (MAXIMUM DETAIL)
        - Create 8-15 micro-steps per task
        - Every physical/mental action gets its own step
        - Eliminate all ambiguity and decision-making
        - Perfect for days with low executive function or high anxiety
        - Focus on starting with the tiniest possible step
        - Format: "**Micro-action**: Exact instructions (where to click/what to say)"
        - Example: "**Click Chrome**: Open new tab → Type 'Warby Parker' → Press Enter"
        """
    
    system_prompt = f"""
    You are a productivity coach specializing in ADHD/autism-friendly task breakdowns. Your output must EXACTLY follow these formatting rules:

    {granularity_instructions}

    1. **BOLD FORMATTING STRATEGY**:
       - Bold the first 2-3 words of every step (action verbs) e.g. "Spend 2 mins", *"Book 10-min try-on"*, "Dump all ideas"
       - Bold all tools/digital aids (apps, websites, programs) e.g. "Google", "Warby Parker Virtual Try-On", "ChatGPT"
       - Bold time/duration mentions (e.g. "2 mins", *"1-hour project"*, "5 mins")
       - Bold system labels (e.g., "Urgent", "Someday")
       - Bold activation hacks (phrases that lower resistance) e.g. "Just find 1 frame you hate", "no commitment"
       - NEVER bold explanatory text, examples in parentheses, or conjunctions

    2. Main Task Headers:
       - CRITICALLY IMPORTANT: First carefully analyze the user's input text to identify ALL potential tasks, even if they are mentioned only briefly or in broken/fragmented English
       - For unclear or ambiguous text, err on the side of generating more tasks rather than fewer
       - Create separate tasks for each distinct activity mentioned by the user
       - Number each task (1., 2., etc.)
       - Use this exact format: "Task: "[Task name]" ([brief description])"
       - Example: "Task: "Buy Spectacles (Don't Know What Frames Are Nice)"

    3. Task Extraction Guidelines:
       - Look for action verbs and nouns that suggest activities
       - Consider "try X" or "use Y" as potential tasks, even if mentioned in passing
       - If user mentions software, apps, products, or services (like "ChatGPT", "Claude", "Cursor AI"), create a task for using/trying them
       - For lists or bullet points, create a task for each distinct item
       - For unclear text, make a reasonable interpretation and create appropriate tasks

    4. Robotic Mode Section:
       - Use header: "Robotic Mode (For [specific purpose]):"
       - Create the appropriate number of steps based on the granularity level selected
       - Bold key words
       - Use large arrows (→⟶➡) between main actions
       - Include time-based cues like "Tomorrow:"
       - For complex steps, use indented bullet points with colored circles (🟢, 🟡, 🔴)

    5. Creative Mode Section:
       - Use header: "Creative Mode (Explore Options):" or similar descriptive subtitle
       - Use bullet points (•) with emoji prefixes
       - Italicize app names
       - Use quotes for suggested phrases or searches
       - Can include any number of options
       - Suggest what people usually do in this situation
       - Include a visual aid like a diagram, chart, or table if relevant

    6. Activation Hack Section:
       - Always include this as a separate section at the end of each task
       - Format: "Activation Hack: "[short, quotation-marked suggestion]"
       - Keep very brief and low-effort

    7. Visual Hierarchy:
       - Use consistent spacing between sections
       - Keep lines short (under 70 characters)
       - Use emojis as visual anchors
       - Bold critical information

    8. Edge Cases:
       - If user text has typos, unusual spacing, or grammatical errors, still identify the key tasks

    Your output will be shown to ADHD users who need clear visual organization and minimal cognitive load.
    """
    
    # Example response format - exactly matching the expected output
    example_response = """
    {
        "Task: \\"Buy Spectacles (Don't Know What Frames Are Nice)\\"": {
            "Robotic Mode (For Paralysis)": [
                "1. Spend 2 mins: Google \\"best glasses for [face shape]\\" → Screenshot 1-2 frames you like.",
                "2. Tomorrow: Show screenshots to a friend (text: \\"Which of these suits me?\\").",
                "3. Next day: Book 10-min try-on at nearest optician (link to book).",
                "4. Try on at least 3 frames and take photos."
            ],
            "Creative Mode (Explore Options)": [
                "🎥 Watch \\"How to Pick Glasses\\" by [YouTube stylist] (8 mins).",
                "📱 *Use \\"Warby Parker Virtual Try-On\\" app* (play with 5 frames).",
                "💡 Ask ChatGPT: \\"I like [description]. Suggest frame styles?\\"",
                "🔍 Browse Pinterest for \\"glasses for [face shape]\\" inspiration.",
                "👁️ Make a list of pros and cons for each frame."
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
        # client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
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
st.markdown("### 💡 Tip:")
st.info(display_random_tip())

# Random affirmation
st.markdown("### 💖 You are loved. You are enough. You are not alone.")
st.success(display_adhd_affirmation())

# Add a section for logs with expander
# with st.expander("View Logs & Debug Info", expanded=False):
#     display_logs()
#     if st.button("Clear Logs"):
#         st.session_state.logs = []

mode = ["🤖 Robotic: Hyper-specific, minimal decision making, lowest activation energy", "🎨 Creative: Multiple approaches with visual aids and technology options"]
log_entry(f"Mode selected: {mode}")

# Explain modes
# if mode == "🤖 Robotic":
#     st.caption("Robotic Mode: Hyper-specific, minimal decision making, lowest activation energy")
# else:
#     st.caption("Creative Mode: Multiple approaches with visual aids and technology options")

# Add a slider in the sidebar for task granularity level
st.sidebar.markdown("### Task Granularity")
granularity_level = st.sidebar.slider(
    "How detailed should your task breakdown be?", 
    min_value=1, 
    max_value=3, 
    value=2,  # Default to medium granularity
    help="Level 1: Minimal steps | Level 2: Moderate breakdown | Level 3: Maximum detail for executive dysfunction"
)

st.sidebar.markdown("""
**Level 1:** Minimal steps for quick overview  
**Level 2:** Balanced breakdown with clear steps  
**Level 3:** Ultra-detailed micro-steps for low executive function days
""")

# Store the selected granularity in session state
if 'granularity_level' not in st.session_state:
    st.session_state.granularity_level = granularity_level
else:
    st.session_state.granularity_level = granularity_level

user_input = st.text_area("Brain Dump here:", 
                         placeholder="e.g., 'it's a good day but wah stress leh need to do taxes, call mom, fix bike, learn piano...I feel overwhelmed'",
                         height=300)

# Update the main button handler:
if st.button("✨ Process My Chaos"):
    log_entry("Process button clicked")
    if user_input:
        log_entry(f"Processing input: '{user_input}'")
        
        # Get emotional validation
        validation = get_emotional_validation(user_input)
        if validation:
            st.markdown(f"""<div style="background-color: #f8f9fa; padding: 15px; 
                        border-radius: 10px; margin-bottom: 20px; border-left: 4px solid #4CAF50;">
                        {validation}</div>""", unsafe_allow_html=True)
        
        # Get task breakdown
        response = get_ai_response(user_input, mode)
        
        # Store the raw response in session state for logging
        if 'raw_model_response' not in st.session_state:
            st.session_state.raw_model_response = response
        else:
            st.session_state.raw_model_response = response

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
    tasks = st.session_state.last_tasks  # Define tasks first
    
    # Now you can use the tasks variable
    st.subheader(f"Your Recommended AI-Generated Action Plan: ({len(tasks)} tasks)")
    
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
        
        # Only show details if expanded
        with st.expander(f"**{task_index}. {clean_task_name}**", expanded=False):
            # Robotic Mode
            if any(key.startswith("Robotic Mode") for key in modes.keys()):
                # Find the key that starts with "Robotic Mode"
                robotic_key = next((key for key in modes.keys() if key.startswith("Robotic Mode")), None)
                if robotic_key:
                    # Clean up the key - remove any trailing colons
                    display_key = robotic_key.rstrip(':')
                    st.markdown(f"<div class='mode-header'>{display_key}:</div>", unsafe_allow_html=True)
                    
                    # Display each step with proper styling
                    for i, step in enumerate(modes[robotic_key]):
                        step_key = f"task_{task_index}_robotic_{i}" 
                        # Initialize checkbox state if it doesn't exist
                        if step_key not in st.session_state.task_states:
                            st.session_state.task_states[step_key] = False
                        
                        # Check if step already starts with a number (like "1.")
                        if re.match(r'^\d+\.', step.strip()):
                            # Already has a number, use as is
                            display_step = re.sub(r'^(\d+)\.', r'\1\\.', step.strip())
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
        
        # Task divider (optional, as expanders already provide visual separation)
        # if task_index < len(tasks):
        #     st.markdown("<hr class='task-divider'>", unsafe_allow_html=True)
        
# Add this at the end of your app after all other UI elements
# with st.expander("🔍 View Raw Model Response", expanded=False):
#     if 'raw_model_response' in st.session_state and st.session_state.raw_model_response:
#         st.code(st.session_state.raw_model_response, language="json")
#     else:
#         st.info("No model response available yet. Process some input to see the raw model output.")
        