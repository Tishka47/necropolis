[app]

# (str) Title of your application
title = Цифровой некрополь

# (str) Package name
package.name = necropolis

# (str) Package domain (needed for android/ios packaging)
package.domain = org.necropolis

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,kv,ttf,txt,png,jpg

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = .venv, __pycache__, bin, .buildozer

# (str) Application versioning
version = 1.0

# (list) Application requirements
# Без charset-normalizer: python-for-android подставляет для него Android-wheel, который pip
# при сборке отвергает. requests в этом случае сам использует chardet (он уже в сборке).
requirements = python3,kivy==2.3.1,requests,urllib3,certifi,chardet,idna

# (list) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = android.permission.INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 24

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) Accept SDK license automatically
android.accept_sdk_license = True

# Сервер в локальной сети работает по http://, а Android 9+ по умолчанию запрещает
# незашифрованный трафик. Файл добавляет android:usesCleartextTraffic="true" в <application>.
android.extra_manifest_application_arguments = ./src/android/extra_manifest_application_arguments.xml

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
