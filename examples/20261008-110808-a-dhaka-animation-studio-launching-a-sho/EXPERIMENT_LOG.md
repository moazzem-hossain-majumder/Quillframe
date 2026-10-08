# Experiment log: Currents of Silt

- Date: 2026-10-08 11:10 Bangladesh Standard Time
- Total pipeline time: 154.4s

**Brand brief**

> A Dhaka animation studio launching a short film about river life, for young festival audiences

## Text model comparison (campaign brief)

| Provider | Model | Latency (s) | Valid output | First slogan / error |
|---|---|---|---|---|
| gemini | gemini-3.8-flash | 43.28 | yes | Every droplet remembers who we are. |
| groq | openai/gpt-oss-120b | 3.05 | yes | Feel the Flow, Own the Story |
| openrouter | nvidia/nemotron-3.5-lightning:free | 89.63 | no | invalid JSON/schema: 1 validation error for CampaignBrief tone   Input should be a valid … |

- Schema-valid answers: 2/3
- Fastest valid answer: groq (3.05s)
- Used for the campaign: gemini

## Social media pack

Providers were tried in order until one gave valid output.

| Provider | Model | Latency (s) | Valid output | Error |
|---|---|---|---|---|
| gemini | gemini-3.8-flash | 60.91 | no | ReadTimeout |
| groq | openai/gpt-oss-120b | 3.52 | yes |  |

## Image generation

| Provider | Model | Prompt # | Latency (s) | File | Error | Prompt |
|---|---|---|---|---|---|---|
| pollinations | flux | 1 | 3.30 | [image_1_pollinations.jpg](images/image_1_pollinations.jpg) |  | A traditional wooden riverboat gliding across misty river waters at dusk, wide cinematic … |
| pollinations | flux | 2 | 2.95 | [image_2_pollinations.jpg](images/image_2_pollinations.jpg) |  | Close-up of a young person hand-trailing through flowing river water, with glowing aquati… |

- pollinations: 2/2 succeeded, average 3.12s per image

## Voiceover (edge-tts)

- Voice: `en-US-AriaNeural`
- Latency: 3.13s
- File: [voiceover.mp3](voiceover.mp3)

## Your notes

### Key observations

- **Image generation (Pollinations Flux)**: Both prompts completed with 100% success rate (2/2) at an average of **3.12s** per image.
  - *Prompt 1 (3.30s)*: Produced a haunting, misty wide shot of a traditional wooden riverboat reflecting gentle light on the water.
  - *Prompt 2 (2.95s)*: Created a striking visual of glowing, bioluminescent turquoise currents swirling through the river depth, matching the folklore theme.
  - *Fix applied*: Adding HTTP `402` to retry statuses and a 2.0s spacing interval between sequential image requests completely solved the free-tier rate-limit issue.
- **Groq (`openai/gpt-oss-120b`)**: Consistently the fastest text engine across all runs (**3.05s** for brief, **3.52s** for social pack) with clean JSON format compliance (*"Feel the Flow, Own the Story"*).
- **Gemini (`gemini-3.8-flash`)**: Successfully crafted the winning campaign brief (*"Currents of Silt"*) with deep thematic resonance (*"Every droplet remembers who we are"*) and vivid visual directions. Encountered a read timeout on social pack generation under load, triggering an automatic fallback to Groq.
- **OpenRouter (`nvidia/nemotron-3.5-lightning:free`)**: Returned expressive creative copy but failed schema validation due to a non-standard tone format; Quillframe handled this parsing failure without halting the run.
- **edge-tts**: Fast, reliable speech synthesis (**3.13s**) producing clean MP3 voiceover narration.

### What I would try next

1. **Schema coercion for free models**: Add pre-validation transformers to coerce free-form tone/audience outputs from smaller models before schema validation.
2. **Audio localization**: Introduce multilingual audio options with Bangladeshi voice presets (`bn-BD-NabanitaNeural`).
3. **Multi-provider image fallback**: Chain Pollinations with Hugging Face FLUX.1-schnell to provide automatic failover across different endpoints.
