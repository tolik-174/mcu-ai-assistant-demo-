# MCU Assistant — Quick Installation Guide

This guide explains how to install and configure MCU Assistant from the provided VSIX package.

---

# 1. Install Required Software

Before using MCU Assistant, install the following software.

---

## 1.1 Install Visual Studio Code

Download and install VS Code:

https://code.visualstudio.com/

---

## 1.2 Install Docker Desktop

Download Docker Desktop:

https://www.docker.com/products/docker-desktop/

After installation verify Docker:

```bash
docker --version
```
1.3 Install Ollama

Download Ollama:

https://ollama.com/

Verify installation: 
```
ollama --version
```
# 2. Install AI Model

MCU Assistant uses the local Mistral model.

Open terminal and run:
```
ollama pull mistral
```
Wait until the model downloads completely.

You can test it:
```
ollama run mistral
```
Exit using:
```
/bye
```
# 3. Install MCU Assistant Extension

You should receive the extension file:
```
0001-0.0.1.vsix
```
Open VS Code.

Go to:

Extensions → ⋯ → Install from VSIX

Select:
```
0001-0.0.1.vsix
```
Restart VS Code after installation.
# 4. Create Data Folder

Create a folder anywhere on your computer.

Example:

macOS/Linux:
```
/Users/username/mcu-data
```
Windows:
```
C:\mcu-data
```
Inside this folder create the following structure:
```
mcu-data/
├── faiss/
├── parsed/
├── pdf/
└── projects/
    └── zips/
```
4.1 Install backend server 
Install folder 
```
backend
```

# 5. Add Documentation and SDKs
Add PDFs

Copy MCU PDF documentation into:
```
mcu-data/pdf/
```
Example:
```
mcu-data/pdf/STM32_reference_manual.pdf
```
Add SDK ZIP files

Copy SDK ZIP archives into:
```
mcu-data/projects/zips/
```
Example:
```
mcu-data/projects/zips/stm32cube.zip
```
# 6. Build Backend Docker Image

Open terminal.

Go to the backend directory:
```
cd backend
```
Build Docker image:
```
docker build -t mcu-backend .
```
This only needs to be done once.
# 7. Start Backend Container

Run backend container.

IMPORTANT:
Replace the path below with your actual data folder path.

macOS/Linux:
```
docker run -d \
  --name mcu-backend \
  -p 8000:8000 \
  -v /ABSOLUTE/PATH/TO/mcu-data:/app/data \
  mcu-backend
```
Example:
```
docker run -d \
  --name mcu-backend \
  -p 8000:8000 \
  -v /Users/mac/mcu-data:/app/data \
  mcu-backend
```
Windows PowerShell:
```
docker run -d `
  --name mcu-backend `
  -p 8000:8000 `
  -v C:\mcu-data:/app/data `
  mcu-backend
```
# 8. Configure Extension Settings

Open VS Code settings.

Go to:
```
Settings → Extensions → MCU Assistant
```
Configure the following settings.

MCU Assistant: Server Url

Set:
```
http://127.0.0.1:8000
```
MCU Assistant: Data Root

Set the full path to your data folder.

Example macOS:
```
/Users/mac/mcu-data
```
Example Windows:
```
C:\mcu-data
```
This setting is REQUIRED.

MCU Assistant: Auto Start Backend

Recommended:
```
Enabled
```
# 9. Verify Backend

Open terminal and check:
```
docker ps
```
You should see:
```
mcu-backend
```
Check backend logs:
```
docker logs -f mcu-backend
```
Successful startup:
```
[READY] Loaded XXXX chunks into memory.
INFO: Uvicorn running on http://0.0.0.0:8000
```
# 10.Configuring MCU Assistant
Open the user interface settings window (Preferences / Settings UI):
```
Press Ctrl + Shift + P
```
Find and open “Preferences: 
```
Open Settings (UI)”
Go to the “Extensions” section.
Find the MCU Assistant extension.
```
Find the setting:
MCU Assistant: Data Root
(Local path to MCU Assistant data folder)

Set the path to your data folder, for example:
```
/Users/mac/bakalarska/0001/data
```
# 11. Backend Commands

Available commands:
```
MCU Assistant: Backend Status
MCU Assistant: Start Backend
MCU Assistant: Stop Backend
MCU Assistant: Restart Backend
```
