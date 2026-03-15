# MCU AI Assistant – Local Demo Setup

AI assistant for **STM32 documentation and code search inside VS Code**.

The system consists of:

- VS Code Extension (chat + inline suggestions)
- Python Backend (documentation + code search)
- Local LLM via Ollama

This project can be started in **two ways**:

1. **Manual startup** — step by step  
2. **Automatic startup** — using `run_demo.sh`

---

# 1. Requirements

Install the following software.

## Node.js
Install from: https://nodejs.org  
Recommended version: **Node.js 18+**

Check installation:
node -v  
npm -v

---

## Python
Required version: **Python 3.10+**

Check installation:
python3 --version

---

## Ollama
Install from: https://ollama.com

Check installation:
ollama --version

---

# 2. Project Structure

Expected project structure:

mcu-ai-assistant-demo  
│  
├── backend  
│   ├── app.py  
│   ├── code_search.py  
│   └── requirements.txt  
│  
├── data  
│   ├── pdf  
│   ├── parsed  
│   ├── faiss  
│   └── projects  
│       └── zips  
│  
├── src  
│   ├── extension.ts  
│   ├── chat.ts  
│   ├── inlineProvider.ts  
│   └── webview  
│  
├── dist  
├── esbuild.js  
├── package.json  
├── tsconfig.json  
├── README.md  
└── run_demo.sh  

Purpose of `data/` folders:

pdf – documentation files  
parsed – parsed register JSON  
faiss – vector indexes  
projects/zips – example firmware projects  

---

# 3. Install AI Model

Pull the model used by the extension:

ollama pull mistral

Optional test:

ollama run mistral

Stop it with:

Ctrl + C

---

# 4. Two Startup Methods

You can run the project in two ways:

1. **Manual Startup**
2. **Automatic Startup with run_demo.sh**

---

# 5. Method 1 – Manual Startup

Step 1 — Open project root  
Open terminal in the project root folder.

---

Step 2 — Install Node dependencies

npm install

---

Step 3 — Build the VS Code extension

node esbuild.js

This should generate:

dist/extension.js

If this file does not exist the extension will not run.

---

Step 4 — Create Python virtual environment

python3 -m venv .venv

Activate environment.

macOS / Linux:

source .venv/bin/activate

Windows:

.venv\Scripts\activate

After activation terminal should show:

(.venv)

---

Step 5 — Install Python dependencies

python3 -m pip install --upgrade pip  
python3 -m pip install -r backend/requirements.txt

---

Step 6 — Start backend server

cd backend

uvicorn app:app --reload --port 8000

If successful you should see:

Uvicorn running on http://127.0.0.1:8000

Leave this terminal running.

---

Step 7 — Run the extension

Open project in VS Code and press:

F5

This launches:

Extension Development Host

---

Step 8 — Open assistant

In the new VS Code window:

Click the rocket button in the status bar  
or run command:

Open AI

---

# 6. Method 2 – Automatic Startup with run_demo.sh

This method prepares most of the environment automatically.

Step 1 — Give execution permission

chmod +x run_demo.sh

Run this once.

---

Step 2 — Start demo launcher

./run_demo.sh

The script will automatically:

- check Node.js
- check Python
- check Ollama
- install Node dependencies
- build the extension
- create `.venv` if missing
- install Python dependencies
- download mistral model if needed
- start backend server

After the script finishes setup it will display:

http://127.0.0.1:8000

Then open VS Code and press **F5**.

---

# 7. Chat Modes

The assistant has two modes.

Chat Mode

Direct interaction with the LLM.

Example prompt:

Write STM32 GPIO initialization code

---

Docs Mode

Search inside:

- STM32 documentation
- parsed register data
- FAISS documentation database
- embedded SDK example projects

Example prompts:

show timer characteristics table

explain TIM_CR1 register

search file adc_ep.c

search file main.c

---

# 8. Opening Files From Search

If multiple files are found the assistant returns a table:

| ID | Project | Path |

To open a file:

open 0

Replace 0 with the desired file ID.

---

# 9. Inline Code Suggestions

When the assistant returns a code block the extension automatically creates an inline suggestion in the editor.

Press:

Tab

to accept the suggestion.

---

# 10. Example Test Prompts

Documentation queries:

Explain RCC_APB1RSTR register  
Show STM32 timer characteristics table  
Explain TIM_CR1 register bits  

File search:

search file adc_ep.c  
search file uart.c  

Code generation:

Generate UART initialization example for STM32  
Generate ADC read example  

---

# 11. Recommended Demo Workflow

Recommended demo order:

1. Start backend  
2. Build extension  
3. Press F5  
4. Open assistant  
5. Switch to Docs Mode  
6. Test documentation search  
7. Test file search  
8. Test code generation  

Example prompts:

show timer characteristics table  
search file adc_ep.c  
explain TIM_CR1 register  
Generate UART initialization example for STM32  

---

# 12. Troubleshooting

Extension does not start

Ensure file exists:

dist/extension.js

If missing run:

node esbuild.js

---

npm run compile fails because of ESLint

Use direct build:

node esbuild.js

---

Backend not responding

Check backend is running:

http://127.0.0.1:8000

---

Python packages fail on macOS

Use virtual environment:

python3 -m venv .venv  
source .venv/bin/activate  
python3 -m pip install -r backend/requirements.txt  

---

Ollama model missing

ollama pull mistral

---

Chat opens but Docs Mode fails

Ensure backend is running:

cd backend  
uvicorn app:app --reload --port 8000  

---

run_demo.sh does not start

Give execution permission:

chmod +x run_demo.sh

Then run again:

./run_demo.sh

---

# 13. Stop the System

Stop backend:

Ctrl + C

Stop Ollama:

Ctrl + C

---

# 14. Notes

This is a **local demo version**.

Everything runs locally on the same computer:

- VS Code extension
- backend server
- documentation indexes
- FAISS database
- Ollama LLM

Future versions may include:

- Docker deployment
- centralized company server
- SVD viewer
- shared documentation storage
- company-wide project indexing