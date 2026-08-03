

# مستندات پروژه - سیستم احراز هویت JWT با تشخیص دستگاه و CSRF

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![DRF 3.15](https://img.shields.io/badge/DRF-3.15-red.svg)](https://www.django-rest-framework.org/)
[![Tests](https://img.shields.io/badge/tests-50%20passed-brightgreen.svg)]()
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)

## فهرست مطالب
- [معرفی (فارسی)](#معرفی-فارسی)
- [ویژگی‌ها (فارسی)](#ویژگیها-فارسی)
- [معماری (فارسی)](#معماری-فارسی)
- [پیش‌نیازها و نصب (فارسی)](#پیشنیازها-و-نصب-فارسی)
- [اندپوینت‌های API (فارسی)](#اندپوینتهای-api-فارسی)
- [ملاحظات امنیتی (فارسی)](#ملاحظات-امنیتی-فارسی)
- [گزارش تست‌ها (فارسی)](#گزارش-تستها-فارسی)
- [تشکر و قدردانی (فارسی)](#تشکر-و-قدردانی-فارسی)
- [Introduction (English)](#introduction-english)
- [Features (English)](#features-english)
- [Architecture (English)](#architecture-english)
- [Prerequisites & Setup (English)](#prerequisites--setup-english)
- [API Endpoints (English)](#api-endpoints-english)
- [Security Considerations (English)](#security-considerations-english)
- [Test Report (English)](#test-report-english)
- [Acknowledgments (English)](#acknowledgments-english)

---

###  شمای کلی پروژه و  مسیر ها
![Project Map](screenshots/1.png)
![Project Map](screenshots/2.png)
*شمای مدل Profile
![Project Map](screenshots/3.png)

## معرفی (فارسی)

این پروژه یک سیستم احراز هویت کامل و امن برای APIهای مبتنی بر Django REST Framework است که از JSON Web Tokens (JWT) با قابلیت تشخیص نوع دستگاه کاربر (کامپیوتر یا موبایل) استفاده می‌کند.  
بسته به نوع دستگاه، توکن‌ها در کوکی‌های `HttpOnly` (برای مرورگرهای دسکتاپ) یا به‌صورت کلاسیک در هدر `Authorization` (برای اپلیکیشن‌های موبایل) منتقل می‌شوند. همزمان محافظت CSRF برای کلاینت‌های وب فعال است.  
این راهکار با بهره‌گیری از کتابخانه‌های رسمی `djangorestframework-simplejwt` و سازوکار CSRF جنگو پیاده‌سازی شده و آماده استفاده در محیط‌های پروداکشن می‌باشد.

### توسعه‌دهنده
- **ایمیل:** moeinrezaie516@gmail.com  
- **نام پروژه:** DRF JWT Authentication with Device Detection & CSRF

### راهنمایی و همکاری
در فرایند طراحی و توسعه این پروژه از راهنمایی‌ها و کمک‌های فنی مهندس علی بیگدلی (مدرس و مشاور) استفاده شده است. همچنین برای بهبود سرعت در بازنویسی (رفکتور) و افزایش دقت برخی بخش‌ها، از ابزارهای هوش مصنوعی به صورت محدود کمک گرفته شده است.

---

## ویژگی‌ها (فارسی)
- **احراز هویت دوگانه بر اساس دستگاه:**  
  - مرورگرهای دسکتاپ: توکن‌ها در کوکی‌های امن `HttpOnly`, `Secure`, `SameSite=Lax` قرار می‌گیرند.  
  - موبایل/تبلت: توکن‌ها به صورت کلاسیک از طریق هدر `Authorization: Bearer <token>` و بدنه JSON دریافت و ارسال می‌شوند.
- **محافظت CSRF یکپارچه:**  
  میدلور تشخیص دستگاه، برای کلاینت‌های موبایل بررسی CSRF را غیرفعال می‌کند و برای وب، الزام به ارسال هدر `X-CSRFToken` را حفظ می‌کند.
- **چرخش خودکار Refresh Token و بلاک‌لیست:**  
  با هر بار تمدید توکن، یک `refresh` جدید صادر و توکن قبلی به صورت خودکار بلاک‌لیست می‌شود (با استفاده از `ROTATE_REFRESH_TOKENS` و `BLACKLIST_AFTER_ROTATION`).
- **خروج امن و بلاک‌لیست دستی:**  
  امکان بلاک‌لیست کردن دستی توکن در زمان خروج کاربر.
- **بلاک‌لیست کامل توکن‌های کاربر:**  
  هنگام تغییر رمز عبور یا دیگر رخدادهای حساس، تمامی توکن‌های معتبر کاربر باطل می‌شوند.
- **مدیریت کاربری پیشرفته:**  
  شامل ثبت‌نام، ورود، تغییر رمز عبور، فراموشی و بازیابی رمز عبور، مشاهده و ویرایش پروفایل.
- **سطوح دسترسی انعطاف‌پذیر:**  
  گروه‌ها و مجوزهای سفارشی (admin, support, custom admin و ...).
- **API مستندسازی شده:**  
  استفاده از Swagger (drf-yasg) و/یا drf-spectacular برای نمایش اندپوینت‌ها.
- **آماده برای محیط‌های Docker:**  
  تنظیمات کامل جهت اجرا با Docker و Docker Compose.

---

## معماری (فارسی)

### ساختار پروژه
```
core_project/
├── config/                 # تنظیمات اصلی پروژه (settings, urls, wsgi)
├── accounts/               # اپلیکیشن اصلی احراز هویت
│   ├── models.py           # مدل User (CustomUser) و Profile
│   ├── managers.py         # UserManager سفارشی
│   ├── signals.py          # سیگنال‌های ساخت پروفایل و بلاک‌لیست توکن‌ها
│   ├── middleware.py       # میدلور تشخیص نوع دستگاه
│   └── api/v1/
│       ├── urls.py         # مسیرهای API نسخه ۱
│       ├── views.py        # ویوهای اصلی (Login, Register, Refresh, ...)
│       ├── serializers.py  # سریالایزرهای ورودی/خروجی
│       ├── authentication.py # کلاس احراز هویت سفارشی JWT
│       ├── permissions.py  # سطوح دسترسی (Admin, Support, ...)
│       └── utils.py        # توابع کمکی (ایمیل، blacklist)
└── Dockerfile / docker-compose.yml
```

### جریان کلی
1. **میدلور DeviceDetectionMiddleware** در ابتدای هر درخواست، `User-Agent` را تحلیل کرده و `request.device_type` را برابر `'web'` یا `'mobile'` قرار می‌دهد.  
2. **کلاس احراز هویت سفارشی** (`CookieOrHeaderJWTAuthentication`) بر اساس این نوع دستگاه، توکن `access` را از کوکی یا هدر `Authorization` استخراج می‌کند.  
3. **ویوهای ورود/ثبت‌نام** پس از تولید توکن، در صورت وب بودن کاربر، توکن‌ها را در کوکی‌های `HttpOnly` تنظیم می‌کنند و در غیر این صورت در بدنه JSON برمی‌گردانند.  
4. **ویو تمدید توکن** توکن قبلی را (با توجه به تنظیمات) بلاک‌لیست کرده و یک جفت توکن جدید ایجاد می‌کند.  
5. **سیگنال‌ها** به‌طور خودکار پروفایل کاربر را ایجاد کرده و هنگام تغییر رمز عبور، تمام توکن‌های معتبر کاربر را باطل می‌کنند.

---

## پیش‌نیازها و نصب (فارسی)

### پیش‌نیازها
- Python 3.10+
- pip
- Docker (اختیاری)

### راه‌اندازی
1. پروژه را Clone کنید.
2. یک محیط مجازی بسازید و فعال کنید.
3. وابستگی‌ها را نصب کنید:
   ```bash
   pip install -r requirements.txt
   ```
4. مهاجرت‌ها را اجرا کنید:
   ```bash
   python manage.py migrate
   ```
5. یک ابرکاربر بسازید:
   ```bash
   python manage.py createsuperuser
   ```
6. سرور توسعه را اجرا کنید:
   ```bash
   python manage.py runserver
   ```
   (برای اجرا با Docker: `docker-compose up --build`)

---

## اندپوینت‌های API (فارسی)
همه مسیرها تحت `/api/auth/` در دسترس هستند.

| روش   | مسیر                | توضیح                                | نیاز به احراز |
|-------|---------------------|--------------------------------------|---------------|
| GET   | `/csrf/`            | دریافت کوکی CSRF                     | خیر           |
| POST  | `/register/`        | ثبت‌نام کاربر جدید و دریافت توکن     | خیر           |
| POST  | `/login/`           | ورود و دریافت توکن                   | خیر           |
| POST  | `/logout/`          | خروج و بلاک‌لیست توکن رفرش           | بله           |
| POST  | `/refresh/`         | تمدید توکن (چرخش و بلاک‌لیست خودکار) | خیر           |
| POST  | `/change-password/` | تغییر رمز عبور کاربر جاری            | بله           |
| POST  | `/forgot-password/` | درخواست بازنشانی رمز عبور (ایمیل)    | خیر           |
| POST  | `/reset-password/`  | تأیید و تنظیم رمز جدید               | خیر           |
| GET/PUT | `/profile/`        | مشاهده و ویرایش پروفایل              | بله           |

---

## ملاحظات امنیتی (فارسی)
- کوکی‌های JWT به صورت `HttpOnly`, `Secure` (در پروداکشن) و `SameSite=Lax` تنظیم می‌شوند تا از دسترسی جاوااسکریپت و حملات CSRF محافظت شود.
- کوکی CSRF برای مرورگرها به‌صورت `HttpOnly=False` تنظیم شده تا کتابخانه‌های فرانت‌اند بتوانند مقدار آن را خوانده و در هدر `X-CSRFToken` ارسال کنند.
- میدلور تشخیص دستگاه، بررسی CSRF را برای کلاینت‌های موبایل (که فاقد محیط مرورگری هستند) غیرفعال می‌کند.
- تمامی ورودی‌ها توسط سریالایزرهای معتبر تأیید می‌شوند.
- درخواست‌های فراموشی رمز عبور، برای جلوگیری از افشای اطلاعات، همواره پاسخ یکسان می‌دهند.
- فیلدهای حساس با `sensitive_post_parameters` نشان‌گذاری شده‌اند تا در گزارش‌های خطا نمایش داده نشوند.

---

## گزارش تست‌ها (فارسی)

این پروژه دارای مجموعه‌ای کامل از **۵۰ تست واحد (Unit Tests) و تست‌های امنیتی** است که به صورت خودکار با استفاده از Django Test Framework اجرا می‌شوند.

**وضعیت نهایی:** ✅ تمام ۵۰ تست با موفقیت پاس شدند  
**تاریخ آخرین اجرا:** ۲۰۲۶-۰۸-۰۳  
**محیط اجرا:** Docker – Django 5.2, Python 3.12, SQLite (in-memory)

### 📊 خلاصهٔ تست‌ها

| مجموعه تست (Test Suite) | تعداد تست | توضیح |
|-------------------------|-----------|-------|
| `test_models.py` | ۱۱ | تست مدل User سفارشی، ایجاد کاربر، سوپریوزر، Profile و سیگنال‌ها |
| `test_serializers.py` | ۱۶ | اعتبارسنجی Register, Login, ChangePassword, Profile, Refresh serializers |
| `test_auth.py` | ۱۶ | تست تمام endpointهای احراز هویت (ثبت‌نام، ورود، خروج، CSRF، refresh، تغییر رمز، پروفایل) |
| `test_security.py` | ۷ | تست ویژگی‌های امنیتی: Fingerprint, Rate Limiting, Logout همه دستگاه‌ها, Blacklist پس از تغییر رمز |
| **مجموع** | **۵۰** | **۰ خطا (OK)** |

### 🔍 پوشش تست‌ها (What is tested)

#### ۱. مدل‌ها (`test_models.py`)
- ایجاد کاربر معمولی و سوپریوزر
- الزامی بودن ایمیل
- متدهای `has_perm`, `has_module_perms` و خاصیت `is_staff`
- ایجاد خودکار پروفایل توسط سیگنال
- ذخیره و بازیابی فیلدهای پروفایل و زمان‌های `created_at`/`updated_at`
- نام‌های نمایشی فارسی مدل‌ها

#### ۲. سریالایزرها (`test_serializers.py`)
- **RegisterSerializer:** ثبت‌نام موفق، ایمیل تکراری، عدم تطابق رمز، رمز ضعیف، برگشت توکن‌های JWT
- **LoginSerializer:** ورود موفق با ایمیل/رمز، اعتبارنامه نامعتبر، کاربر ناموجود
- **ChangePasswordSerializer:** تغییر موفق رمز، رمز قبلی اشتباه، عدم تطابق رمز جدید، رمز جدید ضعیف
- **ProfileSerializer:** بازنمایی صحیح پروفایل، به‌روزرسانی فیلدها، اعتبارسنجی شماره تلفن
- **RefreshSerializer:** (در تست‌های API پوشش داده شده)

#### ۳. endpointهای احراز هویت (`test_auth.py`)
- **ثبت‌نام:** از موبایل (JSON) و وب (کوکی) – موفق و خطاهای اعتبارسنجی
- **ورود:** از موبایل و وب – موفق و خطای اعتبارنامه
- **دریافت CSRF:** برای وب
- **خروج:** blacklist شدن refresh token (موبایل) و پاک شدن کوکی‌ها (وب)
- **تمدید توکن:** چرخش و blacklist خودکار توکن قبلی، رد شدن توکن blacklist شده
- **تغییر رمز عبور:** موفق و blacklist شدن توکن‌های قبلی، رد کردن رمز قدیمی اشتباه
- **پروفایل:** دریافت و به‌روزرسانی، دسترسی غیرمجاز (401)

#### ۴. ویژگی‌های امنیتی (`test_security.py`)
- **Fingerprint:** دسترسی با همان دستگاه (۲۰۰)، تغییر User-Agent → ۴۰۱
- **سازگاری با توکن‌های قدیمی:** توکن بدون اثر انگشت همچنان معتبر است
- **Rate Limiting:** ۵ درخواست لاگین موفق، ششمی → ۴۲۹
- **Logout عادی:** blacklist شدن توکن و رد refresh بعدی
- **Logout از همه دستگاه‌ها:** با `logout_all_devices=true` تمام `OutstandingToken`های کاربر blacklist می‌شوند
- **تغییر رمز:** تمام توکن‌های موجود کاربر blacklist می‌شوند

### ▶️ نحوه اجرای تست‌ها

**با Docker (توصیه شده):**
```bash
docker-compose exec backend python manage.py test accounts -v 2
```

**بدون Docker (محیط لوکال):**
```bash
python manage.py test accounts -v 2
```

### 📝 نکات فنی
- کلید `SIGNING_KEY` در تنظیمات `SIMPLE_JWT` به اندازهٔ کافی بلند تنظیم شده تا هشدار `InsecureKeyLengthWarning` ظاهر نشود.
- در تست‌های Rate Limiting از `@override_settings` برای تنظیم نرخ‌های محدود استفاده شده و `cache` قبل از هر تست پاک می‌شود تا تداخلی پیش نیاید.
- تست‌ها از دیتابیس in-memory SQLite استفاده می‌کنند و هیچ دادهٔ واقعی را تغییر نمی‌دهند.

<details>
<summary>📦 خروجی کامل ترمینال (کلیک کنید)</summary>

```text
Found 50 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..................................................
----------------------------------------------------------------------
Ran 50 tests in 23.116s

OK
Destroying test database for alias 'default'...
```
</details>

---

## تشکر و قدردانی (فارسی)
- خالق و توسعه‌دهنده اصلی: **معین رضایی** (moeinrezaie516@gmail.com)
- راهنمایی و کمک‌های فنی: **مهندس علی بیگدلی**(bigdeli.ali3@gmail.com)
- بهینه‌سازی محدود برخی قطعات کد با کمک ابزارهای هوش مصنوعی برای افزایش سرعت و دقت.

---

## Introduction (English)

This project is a complete, production-ready authentication system for Django REST Framework APIs using JSON Web Tokens (JWT) with automatic device detection (desktop vs mobile). Depending on the client type, tokens are either stored in secure `HttpOnly` cookies (for web browsers) or delivered in the classical `Authorization` header and JSON body (for mobile apps). CSRF protection is fully integrated for web clients using Django's built-in middleware.  
The solution follows official `djangorestframework-simplejwt` documentation and employs token rotation, automatic blacklisting, manual logout, and forced invalidation of all user tokens on password change to ensure maximum security.

### Creator
- **Email:** moeinrezaie516@gmail.com  
- **Project:** DRF JWT Authentication with Device Detection & CSRF

### Guidance & Collaboration
This project was developed with the valuable guidance and technical support of **Engineer Ali Bigdeli**. Additionally, limited artificial intelligence assistance was employed to refactor specific code sections for improved speed and precision.

---

## Features (English)
- **Dual-device token delivery:**  
  - Desktop browsers: tokens in `HttpOnly`, `Secure`, `SameSite=Lax` cookies.  
  - Mobile/tablets: standard `Authorization` header and JSON response body.
- **Integrated CSRF protection:**  
  A custom middleware detects the device; for mobiles it disables CSRF checks, for web it preserves the requirement to send `X-CSRFToken`.
- **Automatic refresh token rotation & blacklisting:**  
  On each refresh request, a new refresh token is issued and the previous one is immediately blacklisted (using `ROTATE_REFRESH_TOKENS` و `BLACKLIST_AFTER_ROTATION`).
- **Secure logout:**  
  Manual token blacklisting on user logout.
- **Mass token invalidation:**  
  All outstanding tokens for a user are blacklisted when their password is changed (via signals).
- **Comprehensive account management:**  
  Registration, login, password change, forgot/reset password flow, profile view/update.
- **Role-based permissions:**  
  Custom groups and permissions (admin, support, custom admin, etc.).
- **API documentation:**  
  Swagger UI (drf-yasg / drf-spectacular).
- **Docker ready:**  
  Dockerfile and docker-compose.yml included for easy containerized deployment.

---

## Architecture (English)

### Project Structure
```
core_project/
├── config/                 # Project configuration (settings, urls, wsgi)
├── accounts/               # Main authentication app
│   ├── models.py           # CustomUser & Profile models
│   ├── managers.py         # Custom user manager
│   ├── signals.py          # Signals for profile creation & token blacklisting
│   ├── middleware.py       # Device detection middleware
│   └── api/v1/
│       ├── urls.py         # v1 API routes
│       ├── views.py        # Core views (Login, Register, Refresh, etc.)
│       ├── serializers.py  # Input/output serializers
│       ├── authentication.py # Custom JWT authentication class
│       ├── permissions.py  # Custom permission classes
│       └── utils.py        # Helper functions (email, blacklist all tokens)
└── Dockerfile / docker-compose.yml
```

### Core Flow
1. **DeviceDetectionMiddleware** inspects `User-Agent` and sets `request.device_type` to `'web'` or `'mobile'`.  
2. **Custom authentication class** (`CookieOrHeaderJWTAuthentication`) retrieves the access token from cookie or `Authorization` header accordingly.  
3. **Login/Register views** issue tokens; if the device is web, they attach tokens as secure cookies; otherwise they return them in JSON.  
4. **Refresh view** blacklists the old refresh token (based on settings) and issues a brand new pair.  
5. **Signals** automatically create user profiles and, upon password change, invalidate all existing tokens for that user.

---

## Prerequisites & Setup (English)

### Requirements
- Python 3.10+
- pip
- Docker (optional)

### Setup Steps
1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run database migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
6. Start the development server:
   ```bash
   python manage.py runserver
   ```
   (For Docker: `docker-compose up --build`)

---

## API Endpoints (English)
All endpoints are under `/api/auth/`.

| Method | Path               | Description                            | Authentication |
|--------|--------------------|----------------------------------------|----------------|
| GET    | `/csrf/`           | Obtain CSRF cookie                     | No             |
| POST   | `/register/`       | Register and receive tokens            | No             |
| POST   | `/login/`          | Login and receive tokens               | No             |
| POST   | `/logout/`         | Logout and blacklist refresh token     | Yes            |
| POST   | `/refresh/`        | Refresh token (rotation & blacklist)   | No             |
| POST   | `/change-password/`| Change current user password           | Yes            |
| POST   | `/forgot-password/`| Request password reset email           | No             |
| POST   | `/reset-password/` | Confirm and set new password           | No             |
| GET/PUT| `/profile/`        | View and update profile                | Yes            |

---

## Security Considerations (English)
- JWT cookies are set as `HttpOnly`, `Secure` (in production), and `SameSite=Lax` to prevent XSS and CSRF attacks.
- The CSRF cookie is `HttpOnly=False` so that frontend frameworks can read it and send it back as `X-CSRFToken` header.
- The device detection middleware disables CSRF enforcement for mobile clients (which do not have browser cookies).
- All inputs are validated through serializers.
- Password reset requests always return a generic message to prevent user enumeration.
- Sensitive fields are hidden from error reports using `sensitive_post_parameters`.

---

## Test Report (English)

This project includes a comprehensive suite of **50 Unit and Security Tests** executed automatically via the Django Test Framework.

**Final Status:** ✅ All 50 tests passed successfully  
**Last Run Date:** 2026-08-03  
**Environment:** Docker – Django 5.2, Python 3.12, SQLite (in-memory)

### 📊 Test Summary

| Test Suite | Test Count | Description |
|------------|------------|-------------|
| `test_models.py` | 11 | Custom User model, user creation, superuser, Profile, and signals |
| `test_serializers.py` | 16 | Validation for Register, Login, ChangePassword, Profile, Refresh serializers |
| `test_auth.py` | 16 | All authentication endpoints (register, login, logout, CSRF, refresh, change password, profile) |
| `test_security.py` | 7 | Security features: Fingerprinting, Rate Limiting, Logout all devices, Blacklist on password change |
| **Total** | **50** | **0 errors (OK)** |

### 🔍 Test Coverage (What is tested)

#### 1. Models (`test_models.py`)
- Regular user and superuser creation
- Email field requirement
- `has_perm`, `has_module_perms` methods and `is_staff` property
- Automatic profile creation via signals
- Profile field storage/retrieval and `created_at`/`updated_at` timestamps
- Persian verbose names for models

#### 2. Serializers (`test_serializers.py`)
- **RegisterSerializer:** Successful registration, duplicate email, password mismatch, weak password, JWT token return
- **LoginSerializer:** Successful login with email/password, invalid credentials, non-existent user
- **ChangePasswordSerializer:** Successful password change, wrong old password, new password mismatch, weak new password
- **ProfileSerializer:** Correct profile representation, field updates, phone number validation
- **RefreshSerializer:** (Covered in API tests)

#### 3. Authentication Endpoints (`test_auth.py`)
- **Registration:** From mobile (JSON) and web (cookie) – success and validation errors
- **Login:** From mobile and web – success and credential errors
- **CSRF retrieval:** For web clients
- **Logout:** Refresh token blacklisting (mobile) and cookie clearing (web)
- **Token refresh:** Rotation and automatic blacklisting of previous token, rejection of blacklisted tokens
- **Password change:** Success with previous token blacklisting, rejection of wrong old password
- **Profile:** Retrieval and update, unauthorized access (401)

#### 4. Security Features (`test_security.py`)
- **Fingerprinting:** Access with same device (200), User-Agent change → 401
- **Legacy token compatibility:** Tokens without fingerprint remain valid
- **Rate Limiting:** 5 successful login requests, 6th → 429
- **Regular Logout:** Token blacklisting and subsequent refresh rejection
- **Logout All Devices:** With `logout_all_devices=true`, all user `OutstandingToken`s are blacklisted
- **Password Change:** All existing user tokens are blacklisted

### ▶️ How to Run Tests

**With Docker (Recommended):**
```bash
docker-compose exec backend python manage.py test accounts -v 2
```

**Without Docker (Local environment):**
```bash
python manage.py test accounts -v 2
```

### 📝 Technical Notes
- The `SIGNING_KEY` in `SIMPLE_JWT` settings is set long enough to prevent `InsecureKeyLengthWarning`.
- Rate Limiting tests use `@override_settings` for custom rates, and `cache` is cleared before each test to prevent interference.
- Tests use an in-memory SQLite database and do not modify any real data.

<details>
<summary>📦 Full Terminal Output (click to expand)</summary>

```text
Found 50 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
..................................................
----------------------------------------------------------------------
Ran 50 tests in 23.116s

OK
Destroying test database for alias 'default'...
```
</details>

---

## Acknowledgments (English)
- **Author & Developer:** Moein Rezaie (moeinrezaie516@gmail.com)
- **Guidance & Technical Support:** Engineer Ali Bigdeli (bigdeli.ali3@gmail.com)
- **Limited AI-assisted refactoring** was employed in some areas to enhance code speed and accuracy.
```

