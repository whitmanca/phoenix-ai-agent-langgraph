# Phoenix Public Safety Agent (Chat Only)


A conversational AI agent built with FastAPI and LangChain and powered by Groq LLMs that provides up to date public safety information for Phoenix, Arizona. 
Helps residents stay informed about recent crime reports, emerging crime trends, and other safety resources such as FEMA's flood zone data.
This version focuses purely on text chat — no map actions or visualization hooks are included.

## Features

- Intent analysis with Phoenix-specific filtering
- Tool execution (geocoding, flood risk, etc.) when relevant
- Direct text responses when tools aren’t needed
- FastAPI backend with a /chat endpoint

## Setup
1. Clone the repo
```
git clone https://github.com/your-username/phoenix-agent.git
cd phoenix-agent
```

2. Create virtual environment
```
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Configure environment

Create a .env file in the project root:
```
# Groq API key
GROQ_API_KEY=your_groq_key_here
```


## Run Locally
Start FastAPI server
```
uvicorn app.main:app --reload
```

Test /chat endpoint
```
curl -X POST "http://127.0.0.1:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
  "message": "What are the recent crime trends in the area surrounding 223 N 7th Ave, Phoenix, Arizona?"
}'
```

Example response:
```
{
  "final_response": "The area surrounding 223 N 7th Ave, Phoenix, Arizona, has experienced various crime trends.
Within the past year, there have been 345 reported incidents, with 147 being theft-related and 105 being disorderly conduct.
Additionally, 43 burglaries and 25 assaults have been reported.
The overall crime rate in the 85003 zip code is 15% higher than the national average.
It's essential to exercise caution, especially at night, and be aware of your surroundings to minimize the risk of becoming a victim of crime."
}
```



## Notes

- This version does not include map actions or visualization.
- Responses unrelated to Phoenix return a polite error message.
- Extend with additional tools or LLM settings by editing phoenix_agent.py.
