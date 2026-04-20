# Примеры оформления исследования

## Дашборд: что внутри

Интерактивная многостраничная Streamlit-аппликация для анализа
концентрации экономической активности в 20 крупнейших агломерациях РФ
(2010–2023, синтетический панельный датасет — 2240 наблюдений
город × год × отрасль).

**Страницы:**
1. **Общий обзор** — KPI, карта, топ-10, динамика HHI/Джини/Primacy, CAGR.
2. **География** — пузырьковая карта, сравнение по округам, scatter
   «население × производительность».
3. **Отраслевая структура** — stacked bar, treemap, тепловая карта LQ, area chart
   эволюции специализации города.
4. **Концентрация и неравенство** — HHI/Джини/Тейл/Primacy, кривая Лоренца,
   rank–size график с оценкой показателя Ципфа и R².
5. **Shift-share анализ** — декомпозиция прироста занятости на NS + IM + CS.
6. **Карточка города** — динамика показателей с подсветкой выбранного города
   на фоне остальных, радар-профиль vs среднее, LQ профиль отраслей.
7. **Методология** — определения и формулы всех индексов (LaTeX-рендеринг).

**Архитектура:**
```
dashboard/
├── app.py                  # st.navigation, роутинг страниц
├── lib/
│   ├── data.py            # генератор панели + st.cache_data
│   ├── metrics.py         # HHI, Джини, Тейл, LQ, shift-share, Zipf, Lorenz, CAGR
│   └── theme.py           # палитра, Plotly-template, CSS-стили
└── views/
    ├── overview.py
    ├── map_view.py
    ├── sectors.py
    ├── concentration.py
    ├── shift_share.py
    ├── city.py
    └── methodology.py
```

## Как получить результат максимально быстро

### PDF статьи — автоматически через GitHub Actions
После мёрджа в `main` workflow `.github/workflows/build-paper.yml` соберёт
`paper/paper.pdf`, положит в артефакты и опубликует на `gh-pages`.
Запустить вручную: **Actions → Build LaTeX paper → Run workflow**.

### Дашборд — один клик на Streamlit Cloud
1. <https://share.streamlit.io> → войти через GitHub.
2. **New app** → репо `jerrylipsiha-lang/claude` → ветка `main` →
   main file `dashboard/app.py`.
3. Получишь публичную ссылку вида `https://<app>.streamlit.app`.

### Локально
```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

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
