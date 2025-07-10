[app]

# (str) Title of your application
title = PDFEditor

# (str) Package name
package.name = pdfeditor

# (str) Package domain (needed for android/ios packaging)
package.domain = org.example

# (str) Source code where the main.py live
source.dir = .

# (list) Application requirements
requirements = python3,kivy==2.2.1,kivymd==1.1.1,python-dateutil,pygments,docutils,Pillow==10.0.0,PyMuPDF==1.23.5,PyPDF2==3.0.1,plyer==2.1.0

# (str) Application versioning (major.minor)
version = 1.0.0

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# (int) Target Android API, should be as high as possible.
android.api = 34

# (int) Minimum API your APK / AAB will support.
android.minapi = 21

# (str) Android build tools version to use
android.build_tools_version = 36.0.0

# (str) Android NDK version to use
android.ndk = 25b

# (str) Android SDK version to use
android.sdk = 33

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (str) Android arch to build for, choices: armeabi-v7a, arm64-v8a, x86, x86_64
android.archs = arm64-v8a

# (bool) enables Android auto backup feature (Android API >=23)
android.allow_backup = True

# (str) The format used to package the app for release mode (aab or apk).
android.release_artifact = apk

# (int) Override build timeout in seconds (default is 0 to use default timeout)
build_timeout = 3600

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
