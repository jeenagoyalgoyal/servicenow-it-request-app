# Publish this project to GitHub (about 2 minutes)

The resume links to: **https://github.com/jeenagoyalgoyal/servicenow-it-request-app**
That link only works after you do these steps.

1. Go to https://github.com/new
   - Repository name: `servicenow-it-request-app`
   - Public
   - Do **not** add a README (this folder already has one)
   - Click **Create repository**
2. In Terminal, run:
   ```
   cd ~/Projects/servicenow-it-request-app
   git init
   git add .
   git commit -m "IT Service Request app for ServiceNow"
   git branch -M main
   git remote add origin https://github.com/jeenagoyalgoyal/servicenow-it-request-app.git
   git push -u origin main
   ```
   If git asks who you are, run this first:
   `git config --global user.name "Jeena Goyal"` and `git config --global user.email "jeenagoyalgoyal@gmail.com"`
   If it asks for a password, use a GitHub Personal Access Token (GitHub > Settings > Developer settings > Tokens).
3. Open the link above to check it works.

## Before your interview
Build the app in your own ServiceNow developer instance using the README steps, and run the ATF tests. The interviewer will ask how the Business Rule, GlideAjax call and Flow work, so make sure you can explain each file.
