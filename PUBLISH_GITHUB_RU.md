# Публикация релиза через GitHub Actions

Репозиторий: `kriskarter/cod2-chat-translator`.

1. Открой вкладку **Actions**.
2. Выбери workflow **Build Windows Release**.
3. Нажми **Run workflow**.
4. Для первого публичного релиза включи **Publish this version as a GitHub Release**.
5. Workflow прогонит тесты на Windows, соберёт EXE и двуязычный Setup, сформирует update ZIP + SHA256 + `update.json` и создаст Release с тегом текущей версии.

Обычный push в `main` только собирает проверочный Windows artifact. Публикация релиза выполняется вручную через workflow_dispatch или при push тега `v*`.
