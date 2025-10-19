# 🛠️ AI Browser Agent - Installation Guide

## ✅ **Quick Setup**

### **1. Prerequisites**
- **Anaconda Python** (recommended) or Python 3.8+
- **Google Chrome** browser
- **macOS** (tested) or Linux

### **2. Install Dependencies**

#### **Option A: Using Anaconda (Recommended)**
```bash
# Install required packages
conda install selenium requests

# Or using pip in conda environment
pip install selenium requests
```

#### **Option B: Using System Python**
```bash
# Install required packages
pip3 install selenium requests
```

### **3. Install ChromeDriver**

#### **Option A: Automatic (Recommended)**
ChromeDriver will be automatically managed by Selenium 4.x

#### **Option B: Manual Installation**
```bash
# Download ChromeDriver from https://chromedriver.chromium.org/
# Place it in your PATH or project directory
```

### **4. Test Installation**
```bash
# Test the AI Browser Agent
./ai_agent.sh "open google.com"
```

## 🔧 **Troubleshooting**

### **Common Issues:**

#### **"No module named 'selenium'"**
```bash
# Install selenium
pip install selenium
# or
conda install selenium
```

#### **"No module named 'requests'"**
```bash
# Install requests  
pip install requests
# or
conda install requests
```

#### **"ChromeDriver not found"**
```bash
# Update selenium (includes ChromeDriver manager)
pip install --upgrade selenium
```

#### **"Chrome not found"**
- Make sure Google Chrome is installed
- Check Chrome path in `chrome_manager.py` if needed

### **Environment Issues:**

#### **Wrong Python Version**
The launcher script automatically detects and uses Anaconda Python. If you have issues:

```bash
# Use full path directly
/opt/anaconda3/bin/python setup_agent.py "your task"

# Or check your Python
which python
python --version
```

#### **Permission Issues**
```bash
# Make scripts executable
chmod +x ai_agent.sh
chmod +x setup_agent.py
```

## 📋 **Verification**

### **Test All Components:**
```bash
# Test Chrome connection
./ai_agent.sh "open google.com"

# Test navigation
./ai_agent.sh "open youtube"

# Test search
./ai_agent.sh "search google for test"
```

### **Expected Output:**
```
🤖 AI Browser Agent Launcher
Using Anaconda Python environment...
✅ Found Anaconda Python
🚀 AI Browser Agent Setup
==================================================
🔧 Checking Chrome status...
✅ Chrome already ready with X tabs
🔗 Connecting to Chrome...
✅ Connected to Chrome!
✅ AI Browser Agent ready!
🎯 Task completed successfully!
```

## 🎯 **Ready to Use!**

Once installation is complete, you can use the AI Browser Agent with simple commands:

```bash
./ai_agent.sh "open gmail"
./ai_agent.sh "search google for Python automation"  
./ai_agent.sh "open telegram.org"
```

The AI Browser Agent will automatically:
- ✅ Connect to your existing Chrome with all logins
- ✅ Navigate to websites reliably
- ✅ Execute tasks autonomously
- ✅ Handle errors gracefully

**Installation complete!** 🚀