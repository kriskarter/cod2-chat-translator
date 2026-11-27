"""Explicit QML labels; untranslated text remains visible instead of blank."""
LABELS = {
    "Главная": ("Home", "Головна"),
    "Серверы": ("Servers", "Сервери"),
    "Настройки": ("Settings", "Налаштування"),
    "История": ("History", "Історія"),
    "О программе": ("About", "Про програму"),
    "Профили": ("Profiles", "Профілі"),
    "База знаний": ("Knowledge base", "База знань"),
    "Уведомления": ("Notifications", "Сповіщення"),
    "Обновления": ("Updates", "Оновлення"),
    "Друг в игре": ("Friend in game", "Друг у грі"),
    "Ошибка": ("Error", "Помилка"),
    "Профили обновлены": ("Profiles refreshed", "Профілі оновлено"),
    "База знаний обновлена": ("Knowledge updated", "Базу знань оновлено"),
    "База знаний актуальна": ("Knowledge up to date", "База знань актуальна"),
    "Доступна стабильная версия": ("Stable release available", "Доступна стабільна версія"),
    "Новых стабильных версий нет": ("No newer stable release", "Нових стабільних версій немає"),
}
def translate(text, language):
    if text in DISPLAY_KEYS:
        text = DISPLAY_KEYS[text]
    if language == "ru" and text in ("online","offline","waiting","limited","unknown"):
        return {"online":"Онлайн","offline":"Офлайн","waiting":"Ожидание","limited":"Ограничено","unknown":"Неизвестно"}[text]
    values = LABELS.get(text)
    return values[0 if language == "en" else 1] if values and language in ("en", "uk") else text

LABELS.update({
    "Translation · разработка": ("Translation · development", "Переклад · розробка"),
    "UDP Monitor · разработка": ("UDP Monitor · development", "UDP Monitor · розробка"),
    "Автоматический выбор активного профиля": ("Automatically select active profile", "Автоматичний вибір активного профілю"),
    "Активен": ("Active", "Активний"),
    "Введите сообщение": ("Enter message", "Введіть повідомлення"),
    "Версия": ("Version", "Версія"),
    "Входящий перевод": ("Incoming translation", "Вхідний переклад"),
    "Выберите сервер": ("Choose a server", "Оберіть сервер"),
    "Выбрать": ("Select", "Обрати"),
    "Выключен": ("Off", "Вимкнено"),
    "Добавить": ("Add", "Додати"),
    "Добавить сервер": ("Add server", "Додати сервер"),
    "Друзья в игре: ": ("Friends in game: ", "Друзі в грі: "),
    "Журнал CoD2 (console_mp.log)": ("CoD2 log (console_mp.log)", "Журнал CoD2 (console_mp.log)"),
    "Записи": ("Entries", "Записи"),
    "Игровой keyboard hook ещё не готов.": ("Game keyboard hook is not ready yet.", "Ігровий keyboard hook ще не готовий."),
    "Игровые F8/F9/F10 подключены · F9 и Enter отправляют только в активную CoD2.": ("F8/F9/F10 connected · F9 and Enter send only to active CoD2.", "Ігрові F8/F9/F10 підключено · F9 та Enter надсилають лише в активну CoD2."),
    "Игровые клавиши выключены в этом запуске.": ("Game hotkeys are disabled for this session.", "Ігрові клавіші вимкнено в цьому сеансі."),
    "Игроки": ("Players", "Гравці"),
    "Игроки на сервере": ("Players on server", "Гравці на сервері"),
    "Избранные игроки": ("Favorite players", "Обрані гравці"),
    "Избранный сервер": ("Favorite server", "Обраний сервер"),
    "Изменения действуют в этой сессии. Существующие файлы настроек не изменяются.": ("Changes apply to this session. Existing settings files are unchanged.", "Зміни діють у цьому сеансі. Наявні файли налаштувань не змінюються."),
    "Изменения только в этой сессии": ("Session-only changes", "Зміни лише в цьому сеансі"),
    "Изолированная тестовая версия. Стабильная установка не изменяется.": ("Isolated test version. The stable installation is unchanged.", "Ізольована тестова версія. Стабільна інсталяція не змінюється."),
    "История входящего перевода": ("Incoming translation history", "Історія вхідного перекладу"),
    "Исходящий перевод": ("Outgoing translation", "Вихідний переклад"),
    "Исходящий перевод · ручной режим": ("Outgoing translation · manual mode", "Вихідний переклад · ручний режим"),
    "Карта": ("Map", "Карта"),
    "Компоненты: визуальная проверка": ("Components: visual check", "Компоненти: візуальна перевірка"),
    "Локальный словарь": ("Local dictionary", "Локальний словник"),
    "Мониторинг серверов": ("Server monitor", "Моніторинг серверів"),
    "Название": ("Name", "Назва"),
    "Название сервера": ("Server name", "Назва сервера"),
    "Найти профили": ("Find profiles", "Знайти профілі"),
    "Настройки перевода": ("Translation settings", "Налаштування перекладу"),
    "Настройки сервера": ("Server settings", "Налаштування сервера"),
    "Настройки сохраняются в отдельном Qt-файле.": ("Settings are stored in a separate Qt file.", "Налаштування зберігаються в окремому Qt-файлі."),
    "Не перенесён": ("Unavailable", "Недоступно"),
    "Ник игрока": ("Player nickname", "Нік гравця"),
    "Новые сообщения появятся здесь": ("New messages will appear here", "Нові повідомлення з'являться тут"),
    "Новых уведомлений нет": ("No new notifications", "Нових сповіщень немає"),
    "Обновить": ("Refresh", "Оновити"),
    "Обновить базу знаний": ("Update knowledge", "Оновити базу знань"),
    "Обновления содержат только проверяемые данные словаря, без исполняемого кода.": ("Updates contain validated dictionary data only, no executable code.", "Оновлення містять лише перевірені дані словника, без виконуваного коду."),
    "Оверлей": ("Overlay", "Оверлей"),
    "Отдельная проверка диалога": ("Separate dialog check", "Окрема перевірка діалогу"),
    "Открыть ручной перевод": ("Open manual translation", "Відкрити ручний переклад"),
    "Отмена": ("Cancel", "Скасувати"),
    "Перевести": ("Translate", "Перекласти"),
    "Перевод текста без отправки в игру": ("Translate text without sending to game", "Переклад тексту без надсилання у гру"),
    "Перевод…": ("Translating…", "Переклад…"),
    "Переименовать": ("Rename", "Перейменувати"),
    "Пинг": ("Ping", "Пінг"),
    "Подключиться": ("Connect", "Підключитися"),
    "Применить": ("Apply", "Застосувати"),
    "Проверить обновления": ("Check for updates", "Перевірити оновлення"),
    "Путь к console_mp.log": ("Path to console_mp.log", "Шлях до console_mp.log"),
    "Режим сравнения": ("Comparison mode", "Режим порівняння"),
    "Русский": ("Russian", "Російська"),
    "Русский → English": ("Russian → English", "Російська → English"),
    "Ручной перевод текста": ("Manual text translation", "Ручний переклад тексту"),
    "Ручной режим не отправляет сообщения в игру.": ("Manual mode does not send messages to the game.", "Ручний режим не надсилає повідомлення у гру."),
    "Сервер": ("Server", "Сервер"),
    "Серверы CoD2": ("CoD2 servers", "Сервери CoD2"),
    "Сообщать о появлении друзей в игре": ("Notify when friends join the game", "Сповіщати про появу друзів у грі"),
    "Сохранить настройки": ("Save settings", "Зберегти налаштування"),
    "Стабильный пакет не устанавливается поверх Qt Preview.": ("Stable packages are not installed over Qt Preview.", "Стабільний пакет не встановлюється поверх Qt Preview."),
    "Статус": ("Status", "Статус"),
    "Убрать": ("Remove", "Прибрати"),
    "Удаление сервера": ("Remove server", "Видалення сервера"),
    "Удалить": ("Delete", "Видалити"),
    "Удалить выбранный сервер из списка?": ("Remove the selected server from the list?", "Видалити обраний сервер зі списку?"),
    "Українська": ("Ukrainian", "Українська"),
    "Чат → ": ("Chat → ", "Чат → "),
    "Чат → русский": ("Chat → Russian", "Чат → російська"),
    "Язык входящего перевода": ("Incoming target language", "Мова вхідного перекладу"),
    "Язык интерфейса": ("Interface language", "Мова інтерфейсу"),
    "демонстрация": ("demo", "демонстрація"),
    "Ожидание запуска": ("Waiting to start", "Очікування запуску"),
    "Настройки сохранены": ("Settings saved", "Налаштування збережено"),
    "Ошибка сохранения: ": ("Save error: ", "Помилка збереження: "),
    "Входящий перевод включён": ("Incoming translation enabled", "Вхідний переклад увімкнено"),
    "Входящий перевод выключен": ("Incoming translation disabled", "Вхідний переклад вимкнено"),
    "Ошибка: ": ("Error: ", "Помилка: "),
    "UDP: ожидание ответа": ("UDP: awaiting response", "UDP: очікування відповіді"),
    "UDP: обновление": ("UDP: refreshing", "UDP: оновлення"),
    "Запуск CoD2": ("Launching CoD2", "Запуск CoD2"),
    "Сервер добавлен": ("Server added", "Сервер додано"),
    "Неверный адрес, повтор или достигнут лимит": ("Invalid address, duplicate or limit reached", "Невірна адреса, повтор або досягнуто ліміт"),
})

LABELS.update({"Вкл": ("On", "Увімк"), "Выкл": ("Off", "Вимк"), "Отображение перевода в игре": ("In-game translation HUD", "Переклад у грі"), "Адаптация игрового текста": ("Gaming language adaptation", "Адаптація ігрового тексту")})

LABELS.update({"Показывать оригинал": ("Show original text", "Показувати оригінал"), "Скрывать выбранный язык": ("Hide target language", "Приховувати обрану мову"), "Игровой сленг": ("Gaming slang", "Ігровий сленг"), "Убирать повторы": ("Suppress duplicates", "Прибирати повтори"), "Настройки HUD": ("HUD settings", "Налаштування HUD"), "Размер текста": ("Text size", "Розмір тексту"), "Время показа": ("Display duration", "Час показу"), "Фон": ("Background", "Тло")})
LABELS.update({
    "Статистика": ("Statistics", "Статистика"),
    "Локальный опыт": ("Local experience", "Локальний досвід"),
    "Собирать примеры локально": ("Collect examples locally", "Збирати приклади локально"),
    "Дисковый кэш на 7 дней": ("Disk cache for 7 days", "Дисковий кеш на 7 днів"),
    "Очистить опыт": ("Clear experience", "Очистити досвід"),
    "Локальный опыт очищен": ("Local experience cleared", "Локальний досвід очищено"),
    "Экспорт сохранён": ("Export saved", "Експорт збережено"),
    "Укажите новый ZIP-файл": ("Choose a new ZIP file", "Вкажіть новий ZIP-файл"),
    "Удалить только локальный опыт и кэш?": ("Delete only local experience and cache?", "Видалити лише локальний досвід і кеш?"),
    "Экспорт ZIP": ("Export ZIP", "Експорт ZIP"),
    "Перед передачей архива проверьте его содержимое. Автоотправки нет.": ("Review the archive before sharing. Nothing is uploaded automatically.", "Перевірте архів перед передаванням. Автоматичного надсилання немає."),
    "Настройки оверлея": ("Overlay settings", "Налаштування оверлею"),
    "Обновить статистику": ("Refresh statistics", "Оновити статистику"),
    "Стили перевода": ("Translation styles", "Стилі перекладу"),
    "Прозрачность фона": ("Background opacity", "Прозорість тла"),
})

LABELS.update({
    "Доступно обновление Qt": ("Qt update available", "Доступне оновлення Qt"),
    "Новых версий Qt нет": ("No newer Qt release", "Нових версій Qt немає"),
    "Открыть страницу обновления": ("Open update page", "Відкрити сторінку оновлення"),
})

LABELS.update({
"Журнал игры": ("Game logging", "Журнал гри"),
"Включить logfile 2 в конфигурациях CoD2? Файлы запущенной игры не изменяются.": ("Enable logfile 2 in CoD2 configuration files? Running game files are not modified.", "Увімкнути logfile 2 у конфігураціях CoD2? Файли запущеної гри не змінюються."),
"После выхода из игры": ("After game exits", "Після виходу з гри"),
"Тест оверлея": ("HUD test", "Тест оверлею"),
"Очистить": ("Clear", "Очистити"),
"Только текст": ("Text only", "Лише текст"),
"Минимальный": ("Minimal", "Мінімальний"),
"Читаемый": ("Readable", "Читабельний"),
"Количество сообщений": ("Message count", "Кількість повідомлень"),
"Ширина": ("Width", "Ширина"),
"Высота": ("Height", "Висота"),
"Плавное исчезновение": ("Fade out", "Плавне зникнення"),
"Компактный фон": ("Compact background", "Компактне тло"),
"Фон только с сообщениями": ("Background with messages only", "Тло лише з повідомленнями"),
"Автоматическая высота": ("Automatic height", "Автоматична висота"),
"Сбросить позицию": ("Reset position", "Скинути позицію"),
})

LABELS.update({
"Ожидание запуска": ("Waiting to start", "Очікування запуску"),
"Настройки сохранены": ("Settings saved", "Налаштування збережено"),
"Ошибка сохранения": ("Save failed", "Помилка збереження"),
"Входящий перевод включён": ("Incoming translation enabled", "Вхідний переклад увімкнено"),
"Входящий перевод выключен": ("Incoming translation disabled", "Вхідний переклад вимкнено"),
"Игровые клавиши готовы": ("Game hotkeys ready", "Ігрові клавіші готові"),
"F9: отправка в CoD2": ("F9: sending to CoD2", "F9: надсилання в CoD2"),
"F9: отправлено": ("F9: sent", "F9: надіслано"),
"F9: ввод отменён": ("F9: input cancelled", "F9: введення скасовано"),
"F9: ввод закрыт": ("F9: input closed", "F9: введення закрито"),
"F9: фокус CoD2 потерян": ("F9: CoD2 focus lost", "F9: фокус CoD2 втрачено"),
"Enter — отправить · Esc — отменить": ("Enter — send · Esc — cancel", "Enter — надіслати · Esc — скасувати"),
"Введите сообщение…": ("Enter message…", "Введіть повідомлення…"),
"Перевод… Esc — отменить": ("Translating… Esc — cancel", "Переклад… Esc — скасувати"),
"Ошибка перевода · повторите Enter": ("Translation failed · retry Enter", "Помилка перекладу · повторіть Enter"),
"Некорректный текст или язык": ("Invalid text or language", "Некоректний текст або мова"),
"UDP: ожидание ответа": ("UDP: waiting for response", "UDP: очікування відповіді"),
"UDP: обновление": ("UDP: refreshing", "UDP: оновлення"),
"Запуск CoD2": ("Starting CoD2", "Запуск CoD2"),
"Ошибка запуска": ("Launch failed", "Помилка запуску"),
"Сервер добавлен": ("Server added", "Сервер додано"),
"Неверный адрес, повтор или достигнут лимит": ("Invalid address, duplicate or limit reached", "Некоректна адреса, повтор або досягнуто ліміт"),
"online": ("Online", "Онлайн"), "offline": ("Offline", "Офлайн"), "waiting": ("Waiting", "Очікування"), "limited": ("Limited", "Обмежено"),
})

LABELS.update({
  "Движок готов": [
    "Engine ready",
    "Двигун готовий"
  ],
  "Требуется настройка": [
    "Setup required",
    "Потрібне налаштування"
  ],
  "Журнал подключён": [
    "Log connected",
    "Журнал підключено"
  ],
  "Журнал не выбран": [
    "Log not selected",
    "Журнал не вибрано"
  ],
  "Игра обнаружена": [
    "Game detected",
    "Гру знайдено"
  ],
  "Игра не обнаружена": [
    "Game not detected",
    "Гру не знайдено"
  ],
  "Ручной перевод": [
    "Manual translation",
    "Ручний переклад"
  ],
  "Никнейм": [
    "Nickname",
    "Нікнейм"
  ],
  "Счёт": [
    "Score",
    "Рахунок"
  ],
  "Нет данных об игроках": [
    "No player data",
    "Немає даних про гравців"
  ],
  "Добавьте сервер": [
    "Add a server",
    "Додайте сервер"
  ]
})

LABELS.update({"Назад":("Back","Назад"),"Понятный":("Clear","Зрозумілий"),"Живой":("Natural","Живий"),"Без цензуры":("Uncensored","Без цензури"),"Профили пока не найдены. Автоматический поиск проверяет установленные игры и журналы. Можно указать путь вручную.":("No profiles found yet. Automatic search checks game installations and logs. You can enter a path manually.","Профілі поки не знайдено. Автоматичний пошук перевіряє встановлені ігри та журнали. Можна вказати шлях вручну."),"Неофициальная утилита. Copyright © 2026 kriskarter. Все права защищены.":("Unofficial utility. Copyright © 2026 kriskarter. All rights reserved.","Неофіційна утиліта. Copyright © 2026 kriskarter. Усі права захищено."),"Поддержка проекта":("Project support","Підтримка проєкту"),"Лицензия":("License","Ліцензія"),"Нет измерений. Включите локальный опыт и обновите статистику.":("No measurements. Enable local experience and refresh statistics.","Немає вимірювань. Увімкніть локальний досвід та оновіть статистику.")})

LABELS.update({
"Перетащите тестовый HUD":("Drag test HUD","Перетягніть тестовий HUD"),
"Оповещение при появлении избранного игрока. Первый опрос сервера не вызывает уведомление.":("Notify when a favorite player joins. The first server poll does not trigger a notice.","Сповіщати при появі обраного гравця. Перше опитування сервера не викликає сповіщення."),
"История текущей сессии · экспорт содержит никнеймы и текст":("Current session history · export includes nicknames and text","Історія поточної сесії · експорт містить нікнейми й текст"),
"Экспорт JSON":("Export JSON","Експорт JSON"),
"Очистить историю?":("Clear history?","Очистити історію?"),
"Удаляются только сообщения текущей сессии.":("Only current-session messages are removed.","Видаляються лише повідомлення поточної сесії."),
"Ожидание сообщений":("Waiting for messages","Очікування повідомлень"),
"Ручной режим":("Manual mode","Ручний режим"),
})

LABELS.update({"Закрыть":["Close","Закрити"],"Поиск по никнейму, а не по уникальному ID. Одинаковые имена могут принадлежать разным игрокам.":["Nickname matching, not unique ID. Identical names can belong to different players.","Пошук за нікнеймом, а не за унікальним ID. Однакові імена можуть належати різним гравцям."],"Добавить в друзья":["Add friend","Додати в друзі"],"Удалить из друзей":["Remove friend","Видалити з друзів"],"Копировать никнейм":["Copy nickname","Копіювати нікнейм"],"Копировать адрес сервера":["Copy server address","Копіювати адресу сервера"],"Подключиться к серверу":["Connect to server","Підключитися до сервера"],"Нет полной информации о серверах":["Incomplete server information","Неповна інформація про сервери"],"Не найден на отслеживаемых серверах":["Not found on tracked servers","Не знайдено на відстежуваних серверах"],"Несколько совпадений никнейма":["Multiple nickname matches","Кілька збігів нікнейма"],"Добавьте друзей звёздочкой в списке игроков или по никнейму.":["Add friends with a star in the roster or by nickname.","Додайте друзів зірочкою у списку гравців або за нікнеймом."],"Уведомления о друзьях":["Friend notifications","Сповіщення про друзів"],"Друг появился":["Friend appeared","Друг з’явився"],"Друг покинул сервер":["Friend left server","Друг залишив сервер"],"Возможный переход друга":["Possible friend server move","Можливий перехід друга"],"Звук уведомлений":["Notification sound","Звук сповіщень"],"Изменения подтверждаются двумя опросами. Недоступность сервера не считается выходом игрока.":["Changes require two polls. An unreachable server is not treated as a player leaving.","Зміни підтверджуються двома опитуваннями. Недоступність сервера не вважається виходом гравця."],"unknown":["Unknown","Невідомо"]})

LABELS.update({"Некорректный никнейм, повтор или лимит друзей":("Invalid nickname, duplicate or friend limit","Некоректний нікнейм, повтор або ліміт друзів")})

LABELS.update({"Авто":("Auto","Авто"),"Выберите игровой журнал в настройках.":("Select the game log in settings.","Виберіть ігровий журнал у налаштуваннях."),"Входящий перевод выключен.":("Incoming translation is disabled.","Вхідний переклад вимкнено."),"Ожидание новых сообщений в игре.":("Waiting for new in-game messages.","Очікування нових повідомлень у грі."),"История хранится только до закрытия приложения.":("History is retained only until the application closes.","Історія зберігається лише до закриття програми.")})

LABELS.update({"Проверка обновлений…":("Checking for updates…","Перевірка оновлень…"),"Скачивание и проверка SHA-256…":("Downloading and verifying SHA-256…","Завантаження та перевірка SHA-256…"),"Загрузка отменена":("Download cancelled","Завантаження скасовано"),"SHA-256 проверен. Можно установить обновление.":("SHA-256 verified. Ready to install.","SHA-256 перевірено. Можна встановити оновлення."),"Установить обновление?":("Install update?","Встановити оновлення?"),"Приложение закроется. Настройки сохранятся. Запустится проверенный установщик Qt Preview.":("The app will close. Settings will be saved. The verified Qt Preview installer will start.","Програма закриється. Налаштування збережуться. Запуститься перевірений інсталятор Qt Preview."),"SHA-256 проверяет целостность, но не является цифровой подписью.":("SHA-256 checks integrity, not a digital signature.","SHA-256 перевіряє цілісність, але не є цифровим підписом."),"Канал обновлений":("Update channel","Канал оновлень"),"Скачать и проверить":("Download and verify","Завантажити й перевірити"),"Установить":("Install","Встановити")})

LABELS.update({'Скорость перевода': ('Translation speed', 'Швидкість перекладу'), 'мс': ('ms', 'мс'), 'Сообщений в локальном опыте': ('Messages in local experience', 'Повідомлень у локальному досвіді'), 'Медиана': ('Median', 'Медіана'), '95% быстрее': ('95% within', '95% у межах'), 'Замеров': ('Measurements', 'Вимірювань'), 'Перевод игрового чата и мониторинг серверов Call of Duty 2.': ('Game chat translation and server monitoring for Call of Duty 2.', 'Переклад ігрового чату та моніторинг серверів Call of Duty 2.'), 'Тест · Сообщение команды': ('Test · Team message', 'Тест · Повідомлення команди')})

LABELS.update({"с": ("s", "с"), "Кэш перевода": ("Translation cache", "Кеш перекладу"), "История уведомлений": ("Notification history", "Історія сповіщень"), "Да": ("Yes", "Так"), "Нет": ("No", "Ні")})


DISPLAY_KEYS = {
    "incoming": "Входящий перевод",
    "outgoing": "Исходящий перевод",
    "translation_error": "Ошибка перевода",
    "translation_service_busy": "Сервис перевода занят",
}

LABELS.update({
    "Из исходного кода": ("Source build", "З вихідного коду"),
    "Ошибка перевода": ("Translation failed", "Помилка перекладу"),
    "Сервис перевода занят": ("Translation service busy", "Сервіс перекладу зайнятий"),
    "UDP: ожидание ответа": ("UDP · Waiting for a reply", "UDP · Очікування відповіді"),
    "UDP: обновление": ("UDP · Refreshing", "UDP · Оновлення"),
    "Сервер добавлен": ("Server added", "Сервер додано"),
    "Неверный адрес, повтор или достигнут лимит": ("Invalid or duplicate address, or server limit reached", "Некоректна чи повторна адреса, або досягнуто ліміту серверів"),
})

LABELS.update({"Ошибка игровых клавиш": ("Game shortcut error", "Помилка ігрових клавіш"), "Последняя игровая клавиша": ("Last game shortcut", "Остання ігрова клавіша")})

LABELS.update({"Перевод чата с любого языка": ("Translate chat from any language", "Переклад чату з будь-якої мови"), "Перевод ваших сообщений": ("Translate your messages", "Переклад ваших повідомлень")})

LABELS.update({"Открыть окно": ("Open window", "Відкрити вікно"), "Выход": ("Quit", "Вихід"), "Друзья": ("Friends", "Друзі")})

LABELS.update({"на русский": ("into Russian", "російською"), "на украинский": ("into Ukrainian", "українською"), "на английский": ("into English", "англійською"), "Перехватчик установлен. Ожидание игровых нажатий.": ("Hook installed. Waiting for game shortcuts.", "Перехоплювач встановлено. Очікування ігрових натискань."), "Открыть журнал клавиш": ("Open shortcut log", "Відкрити журнал клавіш")})

LABELS.update({"Файл игры найден": ("Game file found", "Файл гри знайдено"), "Файл игры не найден": ("Game file not found", "Файл гри не знайдено"), "Ожидание игровой клавиши": ("Waiting for game shortcut", "Очікування ігрової клавіші")})

LABELS.update({
    "IP-адрес или домен": ("IP address or domain", "IP-адреса або домен"),
    "Порт": ("Port", "Порт"),
    "Название (необязательно)": ("Name (optional)", "Назва (необов’язково)"),
    "Вставленный IP:порт имеет приоритет": ("Pasted host:port takes precedence", "Вставлений IP:порт має пріоритет"),
    "Адрес": ("Address", "Адреса"),
})

LABELS.update({
    "F9 · Исходящий перевод": ("F9 · Outgoing translation", "F9 · Вихідний переклад"),
    "Ввод": ("Input", "Введення"),
    "Перевод": ("Translation", "Переклад"),
    "Ошибка отправки · повторите Enter": ("Send failed · retry Enter", "Помилка надсилання · повторіть Enter"),
    "Настройки игрового окна F9": ("F9 game window settings", "Налаштування ігрового вікна F9"),
    "Непрозрачность фона": ("Background opacity", "Непрозорість фону"),
    "Привет, давно не виделись!": ("Hi, long time no see!", "Привіт, давно не бачились!"),
    "Игра запущена": ("Game running", "Гру запущено"),
    "Игра не запущена": ("Game not running", "Гру не запущено"),
    "CoD2 запущена от администратора, а переводчик — нет. Игровые клавиши и отправка могут не работать. По возможности запустите обе программы без повышения прав.": ("CoD2 is elevated but the translator is not. Game shortcuts and sending may fail. Prefer running both without elevation.", "CoD2 запущено від адміністратора, а перекладач — ні. Ігрові клавіші та надсилання можуть не працювати. За можливості запустіть обидві програми без підвищення прав."),
    "Перезапустить переводчик от имени администратора": ("Restart translator as administrator", "Перезапустити перекладач від адміністратора"),
    "Перезапустить от имени администратора?": ("Restart as administrator?", "Перезапустити від адміністратора?"),
    "Настройки сохранятся. Windows запросит подтверждение UAC.": ("Settings will be saved. Windows will ask for UAC confirmation.", "Налаштування збережуться. Windows запросить підтвердження UAC."),
    "Повышение прав отменено или не удалось": ("Elevation cancelled or failed", "Підвищення прав скасовано або не вдалося"),
    "Сбросить": ("Reset", "Скинути"),
    "Размер текста": ("Text size", "Розмір тексту"),
    "Автоматическая высота": ("Automatic height", "Автоматична висота"),
})

LABELS.update({"Несовпадение прав": ("Privilege mismatch", "Невідповідність прав")})
