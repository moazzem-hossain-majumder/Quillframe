# Publishing Quillframe to GitHub (Windows)

## 1. Make sure no secrets are included

`.env` must **not** exist in what you commit. It is listed in `.gitignore`, so this is automatic, but check once:

```powershell
git status
```

`.env` should not appear in the list.

## 2. Create the repository on GitHub

1. Go to <https://github.com/new>.
2. Name: `quillframe`. Visibility: **Public** (so recruiters can see it).
3. Do **not** tick "Add a README", ".gitignore" or "license". The project already has them.
4. Click **Create repository**.

## 3. Push

Run these inside the project folder (replace `YOUR-USERNAME`):

```powershell
git init
git add .
git commit -m "feat: Quillframe, a multi-model creative AI workbench"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/quillframe.git
git push -u origin main
```

If Git says it does not know who you are, set it once:

```powershell
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

GitHub will ask you to sign in in the browser the first time you push.

## 4. Fix the README badge

In `README.md`, replace `<your-username>` in the CI badge line with your GitHub username, then:

```powershell
git add README.md
git commit -m "docs: fix CI badge"
git push
```

After a minute, the **Actions** tab should show the tests running on Ubuntu and Windows.

## 5. Make the repository impressive (do this after your first real run)

Recruiters skim. Give them something to see in 10 seconds.

1. **Run a campaign** with your own keys (`python -m quillframe serve`).
2. **Take a screenshot** of the web UI showing a finished campaign. Save it as `docs/screenshot.png`.
3. **Add it to the README** under the title:
   ```markdown
   ![Quillframe web UI](docs/screenshot.png)
   ```
4. **Commit one real example run.** Copy a good folder from `outputs\` into a new `examples\` folder (it has the images, audio, social posts and `EXPERIMENT_LOG.md`). Recruiters can then see real results without running anything.
5. **Write your own notes** at the bottom of that run's `EXPERIMENT_LOG.md`: which model followed the format best, which image generator looked better, what you would try next. This is the strongest signal that you tested and compared tools rather than just calling an API.
6. On the GitHub repo page, click the gear icon next to **About** and add:
   - Description: *Multi-model creative AI workbench: compare free LLMs and image models, generate campaigns, voiceovers and experiment logs.*
   - Topics: `generative-ai`, `fastapi`, `llm`, `gemini`, `groq`, `python`, `ai-tools`, `creative-technology`
7. **Pin** the repository on your GitHub profile.

```powershell
git add .
git commit -m "docs: add screenshot and an example campaign run"
git push
```

## 6. Using it in your application

- Link the repository in your CV and in the email.
- Suggested sentence for the email: *"I built Quillframe, an open-source tool that compares free LLM and image-generation APIs on the same creative brief, generates campaign assets (images, voiceover, social posts), and writes an experiment log. It is on GitHub: <link>."*
- Be ready to explain: why you validate model output against a schema, how retries and fallbacks work, and what the experiment log showed you about the models you tried.
