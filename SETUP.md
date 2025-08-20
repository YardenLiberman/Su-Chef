# Su-Chef Setup Guide 🚀

This guide will help you set up Su-Chef on your system and get it running properly.

## Prerequisites 📋

- Python 3.7 or higher
- Internet connection for API access
- Microphone (for voice features)
- Speakers/headphones (for voice output)

## Step 1: Install Dependencies 📦

Install all required Python packages:

```bash
pip install -r requirements.txt
```

Or install them individually:

```bash
pip install python-dotenv openai azure-cognitiveservices-speech
```

## Step 2: Get API Keys 🔑

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to API Keys
4. Create a new API key
5. Copy the key (starts with `sk-`)

### Azure Speech Services Key
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a new Speech Services resource
3. Go to "Keys and Endpoint"
4. Copy Key 1 and Region
5. The key looks like: `1234567890abcdef1234567890abcdef`

## Step 3: Configure Environment Variables ⚙️

Create a `.env` file in your project directory:

```env
# OpenAI API Configuration
OPENAI_API_KEY=sk-your_openai_api_key_here

# Azure Speech Services Configuration
SPEECH_KEY=your_azure_speech_key_here
SPEECH_REGION=westeurope
VOICE_NAME=en-US-JennyMultilingualNeural
LANGUAGE=en-US
```

**Important:** Never commit your `.env` file to version control!

## Step 4: Test Your Setup 🧪

Run the setup test to verify everything is working:

```bash
python test_setup.py
```

You should see:
- ✅ All imports successful
- ✅ Database initialized
- ✅ API keys found

## Step 5: Run Su-Chef 🎉

Start the application:

```bash
python su_chef.py
```

## Troubleshooting 🔧

### Common Issues

#### "Module not found" errors
```bash
pip install -r requirements.txt
```

#### "API key not found" errors
- Check your `.env` file exists
- Verify the API key format is correct
- Restart your terminal after creating `.env`

#### Voice not working
- Check microphone permissions
- Verify Azure Speech key is correct
- Check internet connection

#### Recipe generation fails
- Verify OpenAI API key
- Check internet connection
- Check API usage limits

### Getting Help

1. Run `python test_setup.py` to diagnose issues
2. Check the error messages for specific guidance
3. Verify your API keys are correct
4. Ensure all dependencies are installed

## Next Steps 🚀

Once Su-Chef is running:
1. Create your first recipe
2. Try voice-guided cooking
3. Explore saved recipes
4. Customize your preferences

Happy cooking! 👨‍🍳👩‍🍳
