# Remove documentation files from GitHub and push clean code
# Execute this in PowerShell from the supplier-rfp-agent directory

cd "C:\Users\AbilashEEG\Desktop\RFP MANAGEMENT\supplier-rfp-agent"

# Remove the old commit with docs
Write-Host "Removing documentation files from GitHub..." -ForegroundColor Cyan

# Remove documentation files from git history
git rm --cached -r *.md *.txt --ignore-unmatch

# Create new commit
git commit -m "Remove documentation files - keep only code"

# Push to GitHub (force update)
git push -u origin main --force

Write-Host ""
Write-Host "✅ Clean push complete!" -ForegroundColor Green
Write-Host "GitHub now contains only essential code files"
Write-Host ""
Write-Host "Repository: https://github.com/AbilashEG/RFP"
Write-Host ""
