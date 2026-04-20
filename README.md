# Примеры оформления исследования

## Как получить результат максимально быстро

### PDF статьи — автоматически через GitHub Actions
Ничего ставить не надо. После мёрджа в `main` workflow `.github/workflows/build-paper.yml`:
1. соберёт `paper/paper.pdf`,
2. положит его в артефакты запуска (скачивается со страницы Actions),
3. опубликует на ветку `gh-pages` (если включить GitHub Pages в настройках репо — PDF будет доступен по ссылке).

Запустить вручную: вкладка **Actions → Build LaTeX paper → Run workflow**.

### Дашборд — один клик на Streamlit Cloud
1. Зайти на <https://share.streamlit.io> под своим GitHub.
2. **New app** → репо `jerrylipsiha-lang/claude` → ветка `main` → файл `dashboard/app.py`.
3. Готово: получишь публичную ссылку вида `https://<app>.streamlit.app`.

---


## 1. LaTeX-шаблон статьи — `paper/paper.tex`
Шаблон научной статьи по региональной экономике с:
- титульным блоком, аннотацией, ключевыми словами, JEL-кодами
- формулами, таблицей результатов регрессии
- списком литературы через `natbib`

Сборка:
```bash
cd paper
pdflatex paper.tex && pdflatex paper.tex
```
(или открыть в Overleaf — просто загрузить файл)

## 2. Streamlit-дашборд — `dashboard/app.py`
Интерактивный дашборд по агломерациям РФ: карта, рейтинг, динамика, HHI.

Запуск:
```bash
cd dashboard
pip install -r requirements.txt
streamlit run app.py
```
Откроется в браузере на `http://localhost:8501`.

Данные сейчас синтетические — когда будут реальные (Росстат, ЕМИСС),
заменить функцию `load_data()` на чтение CSV.
