# **🤖 Unified AI Shell v5.0 - Comprehensive README**

Welcome to the Unified AI Shell, a next-generation command-line
interface powered by multiple large language models. This shell is
designed to be an intelligent, autonomous partner that can understand
natural language, execute system commands safely, generate code, create
websites, and learn from its interactions to improve over time.

## **🚀 Quick Start**

Getting started is simple. The provided start_shell.sh script automates
the entire setup process.

1.  **Clone/Download the project** into a directory named
    > unified-ai-shell.

2.  **Add your API keys** to config/ultra_config.ini.

3.  **Run the startup script** from your terminal:

\# Make the script executable first\
chmod +x start_shell.sh\
\
\# Run the script to set up the environment and launch the shell\
./start_shell.sh

This script will create a virtual environment, install all dependencies,
and launch the shell.

## **✨ Core Features**

The Unified AI Shell is packed with features designed for power and
usability:

### **🧠 Intelligent Core**

-   **Multi-AI Integration**: Leverages the strengths of **Gemini 1.5
    > Flash** for analysis and creative tasks, and **GPT-OSS-120B (via
    > Groq)** for high-speed execution and coding.

-   **Smart Routing**: Automatically classifies your requests (e.g.,
    > \'analysis\', \'coding\', \'system command\') and routes them to
    > the best-suited AI model.

-   **Learning System**: Persistently tracks the performance of AI
    > models on different tasks and adapts its routing strategy to
    > become more efficient over time.

### **⚡ Automation Engine**

-   **Auto-Execution**: Intelligently detects when a prompt is a direct
    > command (e.g., \"host a web server\" or \"backup my project
    > files\") and executes it automatically.

-   **Task Scheduling**: Run tasks in the background at specified
    > intervals or times.

-   **System Monitoring**: Set up automated watchers for CPU usage, file
    > changes, and more.

### **🛠️ Full System Control**

-   **Safe Command Execution**: Run any shell command directly from the
    > AI prompt.

-   **File & Directory Management**: ls, cd, cp, mv, mkdir, and rm with
    > natural language.

-   **Safety Mode**: Destructive operations like rm require explicit
    > user confirmation to prevent accidents.

-   **System Status**: Get a beautifully formatted overview of your CPU,
    > memory, and disk usage with the status command.

### **🌐 Generative Modules**

-   **Website Generator**: Create a complete, modern, and responsive
    > single-page website from a simple prompt like \"make a website for
    > a local coffee shop\". The shell will generate the HTML/CSS and
    > host it locally for you.

-   **Code Generator**: Ask for a Python script for a specific task
    > (e.g., \"write a script to parse a CSV file\"). The shell
    > generates the code, saves it, and can execute it on your command.

### **🎨 User Experience**

-   **Rich Terminal UI**: All output is styled using rich for
    > readability, with tables, panels, and syntax highlighting.

-   **Context-Aware History**: The shell remembers the context of your
    > conversation.

-   **Robust Error Handling**: Gracefully handles API errors, command
    > failures, and other issues with clear feedback.

## **📁 Project Directory Structure**

The project is organized into a clean, modular structure:

unified-ai-shell/\
├── main.py \# The main entry point to start the application.\
├── requirements.txt \# A list of all necessary Python packages.\
├── start_shell.sh \# The recommended script to set up and run the
shell.\
├── UNIFIED_README.md \# This documentation file.\
\|\
├── config/\
│ ├── ultra_config.ini \# Configuration for API keys, models, and
settings.\
│ └── config_manager.py \# Module to load and manage configuration.\
\|\
├── core/\
│ ├── \_\_init\_\_.py \# Makes \'core\' a Python package.\
│ ├── shell.py \# The central orchestrator of the shell application.\
│ ├── ai_manager.py \# Handles all interactions with the AI models.\
│ ├── system_controller.py# Manages file operations and command
execution.\
│ ├── task_manager.py \# Defines and tracks available tasks.\
│ ├── learning_system.py \# Tracks AI performance and enables learning.\
│ └── automation.py \# Engine for auto-execution and scheduled tasks.\
\|\
├── modules/\
│ ├── \_\_init\_\_.py \# Makes \'modules\' a Python package.\
│ ├── website_generator.py# Logic for creating and hosting websites.\
│ └── code_generator.py \# Logic for generating and running code.\
\|\
├── data/\
│ └── learning.db \# (Auto-generated) The SQLite database for the
learning system.\
\|\
├── generated_code/ \# (Auto-generated) Directory where generated
scripts are saved.\
├── generated_websites/ \# (Auto-generated) Directory where generated
websites are saved.\
└── backups/ \# (Auto-generated) Stores backups created by the shell.

## **⚙️ Installation & Setup**

If you wish to set up the project manually:

1.  **Create a Virtual Environment**:\
    > python3 -m venv venv\
    > source venv/bin/activate

2.  **Install Dependencies**:\
    > pip install -r requirements.txt
