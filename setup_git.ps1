# Настройка Git для проекта
git config --global user.name "Site Junona"
git config --global user.email "admin@junona-school.ru"

Write-Host "Git configuration:"
Write-Host "  user.name = $(git config --global user.name)"
Write-Host "  user.email = $(git config --global user.email)"

# Очистка несуществующих worktrees
Write-Host "`nCleaning worktrees..."
git worktree prune

Write-Host "`nDone! You can now commit changes."
