# PyVault — Flutter وPython لحماية سكربتات `.py`

مشروع Android جديد مستند بصرياً إلى طراز Bynux المرفق: لوحة ليلية زرقاء، خط Tajawal، بطاقات بحواف مستديرة، وأيقونات Vector. أُزيلت الحسابات والسحابة والمكتبات وتشغيل السكربتات. يحتفظ الـNavigation Drawer بتغيير اللغة، القناة الأولى، القناة الثانية، والصلاحيات. لا يطلب التطبيق إذن تخزين واسعاً؛ اختيار المصدر وحفظ الناتج يجريان عبر منتقي ملفات Android النظامي، وصولاً إلى الملفات التي يحددها المستخدم فقط.

## الوظيفة

يختار المستخدم ملف `.py` حتى 32 MiB، ويُعالج محلياً بواسطة Python 3.13 المضمّن عبر Chaquopy. بعد ذلك يفتح التطبيق نافذة حفظ نظامية لملف `.py` جديد. لا يرفع ملفات ولا يتصل التطبيق بخادم ولا يحتاج حساباً. لا توجد صلاحية INTERNET في المشروع؛ رابطا القناتين يفتحان متصفحاً/تطبيقاً خارجياً فقط إذا ضغط المستخدم عليهما.

تُزال docstrings ويُجمع المصدر دون تعطيل عبارات `assert` ثم يُضغط ويُسلسل ككائن bytecode. تشفّر الحمولة باستخدام AES-256-GCM بمفتاح عشوائي خاص بالملف مشتق عبر HKDF-SHA-256. يرفض مفكك التشفير بيانات الحمولة المعدّلة أو المفتاح/بيانات المصادقة غير المطابقة. تم اختيار AEAD واحد صحيح بدلاً من تكديس خوارزميات لا تضيف أمناً حقيقياً.

## الحد الأمني الذي لا يمكن تجاوزه

ملف `.py` مستقل يعمل من دون كلمة مرور أو مفتاح خارجي يجب أن يحمل مادة فك تشفيره، أو يعتمد على سر موجود في بيئة التشغيل. هذا المشروع يضمّن المفتاح داخل الملف بتجزئة/تمويه؛ لا توفر هذه الخطوة سرية تشفيرية إضافية، ولا تمنع محللاً مصمماً من استخراج المفتاح والحمولة المفكوكة أثناء التشغيل. AES-GCM يحمي سرية الحمولة وهي ساكنة، ويكشف تعديلها عند فكها، لكنه لا يمنح سرية مطلقة بعد تسليم loader قادر على فكها ذاتياً. لا أدّعي استحالة الهندسة العكسية.

الملف الناتج ليس ملفاً يعتمد على مكتبات Python القياسية وحدها: يحتاج `cryptography` وقت التشغيل، ولا يقوم بتثبيتها بنفسه. لتشغيله خارج التطبيق يلزم CPython بنفس إصدار **major.minor** الذي أنشأه، مع `cryptography` مثبتة مسبقاً. مثال: `python -m pip install cryptography`. أما Android فلا يأتي مع مفسّر Python عام يشغّل ملفات `.py` تلقائياً؛ يجب أن تتوفر بيئة Python على الهاتف ومتوافقة مع الإصدار والمكتبة. لم يُختبر هذا التشغيل على هاتف فعلي.

## بناء APK من GitHub

1. ارفع محتويات هذا المجلد إلى فرع `main` في مستودع GitHub.
2. من تبويب **Actions** شغّل **Build PyVault Android**، أو ادفع commit إلى `main`.
3. عند نجاح المهمة نزّل artifact باسم `pyvault-arm64-release-apk`.

يبني Workflow إصدار release لمعمارية `arm64-v8a` فقط. لا يشمل x86/x86_64 أو ARM 32-bit. يستخدم Flutter stable وJava 17 وChaquopy 17.2 وPython 3.13. يضمّن `cryptography==42.0.8` لنواة التشفير داخل التطبيق. اختير wheel هذا الإصدار بعد إصدار بناء متوافق مع صفحات ذاكرة Android ذات 16KB في يوليو 2026؛ مع ذلك يلزم اختبار APK الفعلي على أجهزة الهدف. لم تُوفّر هذه البيئة Flutter SDK أو Android SDK، لذا لم أُنتج APK هنا ولم أتمكن من اختبار البناء أو الواجهة على جهاز Android. يجب اعتبار تشغيل Workflow على GitHub خطوة البناء النهائية، لا APK مبنياً مسبقاً.

## اختبار نواة الحماية محلياً

تحتاج إلى Python 3.12+:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
python protect.py script.py -o script_protected.py
python script_protected.py
```

تغطي الاختبارات تشغيل الحمولة، إزالة docstrings، كشف العبث، رفض إصدار Python المختلف، وحد حجم المصدر. شُغّلت في Linux مع CPython 3.12.3 و`cryptography 45.0.7`: **5 اختبارات ناجحة**. لم تُختبر بعد على Windows/macOS أو على Android/CPython 3.13، لذلك لا أدّعي توافقاً غير متحقق منه.

## ملفات المشروع

- `main.dart`: الواجهة العربية/الإنجليزية واختيار الملف وحفظه والدرج الجانبي.
- `protector_core.py`: تشفير الحمولة وتوليد loader بصيغة `.py`.
- `MainActivity.kt.template`: جسر Flutter MethodChannel إلى Chaquopy.
- `prepare_android.py`: إعداد Chaquopy ونسخ نواة Python إلى مشروع Android الذي ينشئه Flutter.
- `.github/workflows/build.yml`: إنشاء هيكل Android وFlutter، الفحص، بناء APK، رفع Artifact وتشغيل اختبارات Python.
- `test_protector.py`: اختبارات وظيفية واختبارات كشف العبث والقيود.
- `protect.py`: أداة سطر الأوامر لحماية ملف `.py`.
- `Tajawal-*.ttf`: خطوط الواجهة.

## مراجع التقنية

- يذكر توثيق `cryptography` أن AEAD يحقق سرية وسلامة النص المشفر والبيانات المصاحبة، وأن AES-GCM يرفض فك النص المعدل [1].
- يوضح توثيق Python أن صيغة `marshal` داخلية وقد تتغير، وأن كائنات الشيفرة غير متوافقة بين إصدارات Python [2].
- يبيّن سجل Chaquopy 17.1 إصدارات Python الحديثة المدعومة، وتحذر من أن توافق 16KB يعتمد أيضاً على Android wheels المستخدمة [3]. أُغلقت مشكلة wheel لـ`cryptography` بعد نشر بناء متوافق لـ42.0.8 [4].
- توثيق File Picker يوضح اختيار الملفات والحفظ عبر واجهة النظام [5].

[1]: https://cryptography.io/en/latest/hazmat/primitives/aead/ "Authenticated encryption in cryptography"
[2]: https://docs.python.org/3/library/marshal.html "Python marshal module"
[3]: https://chaquo.com/chaquopy/doc/current/changelog.html "Chaquopy changelog"
[4]: https://github.com/chaquo/chaquopy/issues/1448 "Chaquopy cryptography wheel 16 KB page alignment"
[5]: https://pub.dev/packages/file_picker "Flutter File Picker"


## arm64-v8a فقط
يُثبَّت `target-platform=android-arm64` في `gradle.properties`، ويُفرَض `abiFilters` على كل أنواع البناء (debug/release)، وتُستبعد مكتبات `armeabi-v7a` و`x86` و`x86_64` من الـAPK، وتفشل خطوة التحقق في الـWorkflow إن ظهرت أي معمارية أخرى.
