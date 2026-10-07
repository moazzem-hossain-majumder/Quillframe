# Experiment log: River Rhythms Dhaka

- Date: 2026-10-08 02:59 Bangladesh Standard Time
- Total pipeline time: 80.4s

**Brand brief**

> A Dhaka animation studio launching a short film about river life, for young festival audiences

## Text model comparison (campaign brief)

| Provider | Model | Latency (s) | Valid output | First slogan / error |
|---|---|---|---|---|
| gemini | gemini-3.8-flash | 56.54 | no | RuntimeError: HTTP 503: {   "error": {     "code": 503,     "message": "This model is cur… |
| groq | openai/gpt-oss-120b | 3.29 | yes | Feel the flow, live the story. |
| openrouter | nvidia/nemotron-3.5-lightning:free | 41.07 | yes | Ride the Pulse. Festival On. |

- Schema-valid answers: 2/3
- Fastest valid answer: groq (3.29s)
- Used for the campaign: groq

## Social media pack

Providers were tried in order until one gave valid output.

| Provider | Model | Latency (s) | Valid output | Error |
|---|---|---|---|---|
| gemini | gemini-3.8-flash | 21.42 | no | RuntimeError: HTTP 503: {   "error": {     "code": 503,     "message": "This model is cur… |
| groq | openai/gpt-oss-120b | 2.40 | yes |  |

## Image generation

| Provider | Model | Prompt # | Latency (s) | File | Error | Prompt |
|---|---|---|---|---|---|---|
| pollinations | flux | 1 | 4.12 | [image_1_pollinations.jpg](images/image_1_pollinations.jpg) |  | A young Bangladeshi boy in a bright yellow shirt rowing a traditional wooden boat down a … |
| pollinations | flux | 2 | 0.69 | failed | RuntimeError: HTTP 402: {} | A bustling riverside market scene at dusk, stalls with colorful fruits and lanterns, loca… |

- pollinations: 1/2 succeeded, average 4.12s per image

## Voiceover (edge-tts)

- Voice: `en-US-AriaNeural`
- Latency: 2.08s
- File: [voiceover.mp3](voiceover.mp3)

## Your notes

### Key observations

- **Groq (`openai/gpt-oss-120b`)**: The clear winner for speed and format adherence in this run. It produced a perfectly formatted JSON brief in **3.29s** and the social pack in **2.40s**. The slogans were punchy, evocative, and tailored to younger audiences (*"Feel the flow, live the story"*).
- **OpenRouter (`nvidia/nemotron-3.5-lightning:free`)**: Successfully adhered to the Pydantic schema on the first attempt with creative festival-ready slogans (*"Ride the Pulse. Festival On."*), though latency was higher (**41.07s**) due to free-tier queuing.
- **Gemini (`gemini-3.8-flash`)**: Encountered a transient `HTTP 503` (high demand) during concurrent requests. This validated the workbench's fault tolerance: instead of crashing the pipeline, the error was captured as structured data, and Quillframe seamlessly fell back to Groq for downstream asset generation.
- **Pollinations (`flux`)**: Generated a stunning, painterly visual of a young boy navigating a traditional wooden boat at golden hour in **4.12s** (`image_1_pollinations.jpg`). Prompt 2 hit a rate limit (`HTTP 402`) on the public endpoint; the UI and logger captured the failure without dropping the rest of the campaign.
- **edge-tts**: Flawless performance (**2.08s**) producing clear narration audio matching the reflective tone of the film script.

### What I would try next

1. **Multi-provider image fallback**: Introduce a fallback queue for images (Pollinations -> Hugging Face FLUX.1-schnell) so rate limits on one provider do not leave missing asset slots.
2. **Localized voice synthesis**: Test native Bengali voices (`bn-BD-NabanitaNeural`) for Bangladesh-themed campaigns to create authentic bilingual audio.
3. **Automated LLM judge**: Add a secondary evaluation pass where a judge model scores candidate slogans on brevity, emotional resonance, and brief adherence.
