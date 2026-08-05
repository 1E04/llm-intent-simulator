# Master's Thesis: LLM-Based Testing System

#### This is the Repository for the implementation scripts and results from the Masterthesis:
#### Conceptual Design of an LLM-Based Testing System for the Automated Evaluation of Intent Recognition in Virtual Assistants for Intelligent Voice Bots

---

## 🚀 Getting Started & Configuration

This project requires API keys to run the User Simulator and the Target Voice Bot. **For security reasons, this repository is configured to use environment variables rather than hardcoded credentials.**

### 1. Environment Setup (Secure Method)
Create a `.env` file in the root directory of the project. This file is ignored by Git and will safely store your local credentials.

Add the following variables to your `.env` file:
```env
SIMULATOR_MODEL_NAME=gpt-5-nano
SIMULATOR_API_KEY=your_simulator_api_key_here
SIMULATOR_BASE_URL=[https://api.openai.com/v1](https://api.openai.com/v1)

TARGET_MODEL_NAME=gpt-5.6-luna
TARGET_API_KEY=your_target_api_key_here
TARGET_BASE_URL=[https://api.openai.com/v1](https://api.openai.com/v1)