"""Tiny KZ/RU dictionary for server-rendered templates.

Kazakh is the default language; Russian is the alternative.
Usage in templates: {{ t("key") }} where `t` is injected per request.
"""

DEFAULT_LANG = "kz"
LANGS = ("kz", "ru")

STRINGS = {
    # generic / nav
    "brand":            {"kz": "Мүмкіндіктер навигаторы", "ru": "Навигатор возможностей"},
    "home":             {"kz": "Басты бет",               "ru": "Главная"},
    "cabinet":          {"kz": "Кабинет",                 "ru": "Кабинет"},
    "admin":            {"kz": "Админ",                   "ru": "Админ"},
    "login":            {"kz": "Кіру",                    "ru": "Вход"},
    "register":         {"kz": "Тіркелу",                 "ru": "Регистрация"},
    "logout":           {"kz": "Шығу",                    "ru": "Выход"},

    # auth form
    "nickname":         {"kz": "Логин",                   "ru": "Логин"},
    "email":            {"kz": "Email",                   "ru": "Email"},
    "phone":            {"kz": "Телефон",                 "ru": "Телефон"},
    "password":         {"kz": "Құпиясөз",                "ru": "Пароль"},
    "password_repeat":  {"kz": "Құпиясөзді қайтала",      "ru": "Повторите пароль"},
    "login_field":      {"kz": "Логин немесе email",      "ru": "Логин или email"},
    "do_register":      {"kz": "Тіркелу",                 "ru": "Зарегистрироваться"},
    "do_login":         {"kz": "Кіру",                    "ru": "Войти"},
    "have_account":     {"kz": "Аккаунтың бар ма? Кіру",  "ru": "Уже есть аккаунт? Войти"},
    "no_account":       {"kz": "Аккаунт жоқ па? Тіркелу", "ru": "Нет аккаунта? Регистрация"},
    "continue_google":  {"kz": "Google арқылы жалғастыру", "ru": "Продолжить через Google"},
    "or":               {"kz": "немесе",                  "ru": "или"},
    "admin_login":      {"kz": "Әкімші кірісі",           "ru": "Вход для администратора"},
    "register_note":    {"kz": "", "ru": ""},
    "google_off_title": {"kz": "Google кірісі бапталмаған", "ru": "Вход через Google не настроен"},
    "google_off_text":  {"kz": "Әкімшіге хабарласыңыз.",   "ru": "Обратитесь к администратору."},

    # cabinet
    "my_requests":      {"kz": "Менің өтінімдерім",       "ru": "Мои заявки"},
    "no_requests":      {"kz": "Әзірге өтінім жоқ.",      "ru": "Заявок пока нет."},
    "change_password":  {"kz": "Құпиясөзді өзгерту",      "ru": "Сменить пароль"},
    "new_password":     {"kz": "Жаңа құпиясөз",           "ru": "Новый пароль"},
    "save":             {"kz": "Сақтау",                  "ru": "Сохранить"},
    "profile":          {"kz": "Профиль",                 "ru": "Профиль"},

    # requests table
    "req_id":           {"kz": "№",                       "ru": "№"},
    "req_date":         {"kz": "Күні",                    "ru": "Дата"},
    "req_name":         {"kz": "Аты",                     "ru": "Имя"},
    "req_service":      {"kz": "Қызмет",                  "ru": "Услуга"},
    "req_message":      {"kz": "Хабарлама",               "ru": "Сообщение"},
    "req_status":       {"kz": "Күйі",                    "ru": "Статус"},
    "req_contact":      {"kz": "Байланыс",                "ru": "Контакты"},
    "req_notes":        {"kz": "Жауаптар",                "ru": "Ответы"},

    # services
    "svc_consultation": {"kz": "Жеке консультация",       "ru": "Личная консультация"},
    "svc_navigator":    {"kz": "Opportunity Navigator",   "ru": "Opportunity Navigator"},
    "svc_support":      {"kz": "Жеке сүйемелдеу",         "ru": "Личное сопровождение"},
    "svc_other":        {"kz": "Басқа",                   "ru": "Другое"},

    # statuses
    "st_new":           {"kz": "Жаңа",                    "ru": "Новая"},
    "st_in_progress":   {"kz": "Жұмыста",                 "ru": "В работе"},
    "st_done":          {"kz": "Аяқталды",               "ru": "Закрыта"},
    "st_rejected":      {"kz": "Қабылданбады",            "ru": "Отклонена"},

    # admin
    "dashboard":        {"kz": "Басқару тақтасы",         "ru": "Панель управления"},
    "all_requests":     {"kz": "Барлық өтінімдер",        "ru": "Все заявки"},
    "total":            {"kz": "Барлығы",                 "ru": "Всего"},
    "search":           {"kz": "Іздеу",                   "ru": "Поиск"},
    "filter_email":     {"kz": "Email бойынша",           "ru": "По email"},
    "filter_all":       {"kz": "Барлығы",                 "ru": "Все"},
    "update_status":    {"kz": "Күйді жаңарту",           "ru": "Обновить статус"},
    "add_note":         {"kz": "Жауап қосу",              "ru": "Добавить ответ"},
    "note_visible":     {"kz": "Клиентке көрсету",        "ru": "Показать клиенту"},
    "client":           {"kz": "Клиент",                  "ru": "Клиент"},
    "anonymous":        {"kz": "Аноним",                  "ru": "Аноним"},

    # messages
    "err_fields":       {"kz": "Барлық өрісті толтырыңыз.",            "ru": "Заполните все поля."},
    "err_pw_match":     {"kz": "Құпиясөздер сәйкес емес.",            "ru": "Пароли не совпадают."},
    "err_pw_short":     {"kz": "Құпиясөз кемінде 6 таңба болсын.",     "ru": "Пароль минимум 6 символов."},
    "err_nick_taken":   {"kz": "Бұл логин бос емес.",                 "ru": "Этот логин занят."},
    "err_login_latin":  {"kz": "Логин тек латын әріптерімен (3-32 таңба).", "ru": "Логин только латиницей (3–32 символа)."},
    "login_hint":       {"kz": "Тек латын әріптері, сандар, . _ -",   "ru": "Только латиница, цифры, . _ -"},
    "err_email_taken":  {"kz": "Бұл email тіркелген.",               "ru": "Этот email уже зарегистрирован."},
    "err_bad_login":    {"kz": "Логин немесе құпиясөз қате.",         "ru": "Неверный логин или пароль."},
    "err_bad_email":    {"kz": "Email форматы қате.",                "ru": "Неверный формат email."},
    "err_bad_phone":    {"kz": "Телефон форматы қате.",              "ru": "Неверный формат телефона."},
    "ok_registered":    {"kz": "Тіркелу сәтті өтті!",               "ru": "Регистрация прошла успешно!"},
    "ok_pw_changed":    {"kz": "Құпиясөз өзгертілді.",              "ru": "Пароль изменён."},
    "ok_status":        {"kz": "Күй жаңартылды.",                   "ru": "Статус обновлён."},
    "ok_note":          {"kz": "Жауап қосылды.",                   "ru": "Ответ добавлен."},
}

SERVICE_KEY = {
    "consultation": "svc_consultation",
    "navigator": "svc_navigator",
    "support": "svc_support",
    "other": "svc_other",
}

STATUS_KEY = {
    "new": "st_new",
    "in_progress": "st_in_progress",
    "done": "st_done",
    "rejected": "st_rejected",
}


def make_translator(lang):
    lang = lang if lang in LANGS else DEFAULT_LANG

    def t(key):
        entry = STRINGS.get(key)
        if not entry:
            return key
        return entry.get(lang, entry.get(DEFAULT_LANG, key))

    return t


def service_label(service, lang):
    return make_translator(lang)(SERVICE_KEY.get(service, "svc_other"))


def status_label(status, lang):
    return make_translator(lang)(STATUS_KEY.get(status, "st_new"))
