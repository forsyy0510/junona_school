# Подключение проекта к новому Git-репозиторию
# Запустите этот скрипт после закрытия Cursor/IDE (чтобы папка .git не была заблокирована).

$ErrorActionPreference = "Stop"
$projectRoot = "e:\site_junona"

Set-Location $projectRoot

if (Test-Path ".git") {
    Write-Host "Удаление старой папки .git..."
    Remove-Item -Path ".git" -Recurse -Force
}

Write-Host "Инициализация нового репозитория..."
git init

git config --global --add safe.directory $projectRoot

Write-Host "Добавление файлов и первый коммит..."
git add .
git commit -m "Initial commit"

Write-Host ""
Write-Host "Готово. Теперь подключите новый удалённый репозиторий:"
Write-Host "  git remote add origin https://github.com/forsyy0510/junona_school.git"
Write-Host "  git branch -M main"
Write-Host "  git push -u origin main"
Write-Host ""
Write-Host "Пример (GitHub):"
Write-Host "  git remote add origin https://github.com/USERNAME/REPO.git"
Write-Host "  git push -u origin main"
