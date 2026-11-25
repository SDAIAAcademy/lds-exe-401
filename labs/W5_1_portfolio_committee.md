---
course: "قيادة مكتب الذكاء الاصطناعي المؤسسي"
code: "LDS-EXE-401"
version: "2027.1.0"
lab: "5.1"
language: "ar"
view: "trainee"
source: "https://sdaiaacademy.github.io/lds-exe-401/labs/W5_1_portfolio_committee.html"
---

# المختبر 5.1 · محاكاة لجنة المحفظة

محاكاة للجنة محفظة الذكاء الاصطناعي في المجموعة: اثنتا عشرة حالة ببيانات اصطناعية للتكلفة والحجم والمخاطر، ومدخلات مباشرة، وقرار يموّل خمس حالات ويوقف واحدة.

الأسبوع 5 · الجلسة 1: لجنة المحفظة

### ستخرج من هذه المحاكاة بـ

- قرار لجنة المحفظة على اثنتي عشرة حالة: خمس ممولة، وواحدة موقوفة، والبقية بالمرشِّح الذي سقطت عنده أو بشرط عودتها.
- القرار المعدّل بعد مدخلين مباشرين، وملف قرارات يفحصه البرنامج: مادة ورقة اللجنة في كتلة التقييم.

## ما تحتاجه

[**portfolio/usecases.csv**الحالات الاثنتا عشرة](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/usecases.csv) [**portfolio/accounts.csv**بنود الحسابات](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/accounts.csv) [**portfolio/value_notes.md**ملاحظات القيمة من أوراق المالكين](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/value_notes.md) [**portfolio/gate_rules.md**المرشِّحات والحساب والترتيب والسقف](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/gate_rules.md) [**portfolio/committee_roles.md**بطاقات الأدوار](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/committee_roles.md) [**portfolio/observer_sheet.md**ما يلاحظه المراقبون](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/observer_sheet.md) [**portfolio/decisions_template.csv**قالب القرارات](https://sdaiaacademy.github.io/lds-exe-401/labs/files/portfolio/decisions_template.csv) [**portfolio/portfolio_calc.py**حاسبة اللجنة](https://sdaiaacademy.github.io/lds-exe-401/labs/portfolio/portfolio_calc.py)

180 دقيقة في لجان من ستة إلى ثمانية. المبالغ بآلاف الريالات إلا ما ذُكر. سياسة الذكاء الاصطناعي: دون ذكاء اصطناعي في أثناء المحاكاة؛ البرامج حاسبات لا نماذج. الملفات اصطناعية ومصنفة «عام».

## الخطوات

### 1 · الإحاطة وتوزيع الأدوار وقراءة الحالات 20 د

يوزع المدرب الأدوار من `committee_roles.md`: رئيس اللجنة (المدير المالي)، والرئيس التنفيذي للبيانات، ورئيس المخاطر والالتزام، ورئيس تقنية المعلومات، ورئيس المكتب أمينًا، ومالكو الحالات (لكل مالك حالتان أو ثلاث)، ومراقب أو اثنان. يقرأ كل دور الحالات بأسئلته.

### 2 · احسب التكلفة لكل نتيجة ناجحة واربط القيمة ببند الحسابات 40 د

انسخ `decisions_template.csv` إلى `my_decisions.csv` في المجلد نفسه. لكل حالة: ابحث عن بندها في `accounts.csv`، واقرأ `value_notes.md`، واكتب في `accepted_value_per_success_sar` ما تقبله اللجنة إن خالف ادعاء المالك. ثم شغّل:

```
# ملف: الطرفية
uv run labs/portfolio/portfolio_calc.py labs/files/portfolio/my_decisions.csv
```

### 3 · طبّق البوابات ومعايير الإيقاف والمرشِّحات 30 د

بالترتيب في `gate_rules.md`: قاعدة البيانات، والمالك، ومعيار الإيقاف، ومستوى الخطر، والقياس. اكتب المرشِّح في عمود `filter` لكل حالة سقطت، وأعد التشغيل. رتّب ما بقي بقاعدة الترتيب أو بسبب مكتوب.

### 4 · الجولة الأولى: عروض المالكين وأسئلة اللجنة 35 د

يعرض كل مالك حالته في ثلاث دقائق، وتسأل اللجنة بأدوارها. يكتب الأمين القرار في عمود `decision` (fund أو stop أو return أو defer) وسببه في `reason`، ويشغّل الحاسبة حتى لا يكتب «problem».

### 5 · مدخلان مباشران: خفض السقف وقيمة يقبلها المدير المالي 25 د

يقرأ المدرب مدخلين. احفظ قرار الجولة الأولى، وانسخه إلى `my_decisions_after.csv`، وأعد الحساب بالسقف الجديد بالخيار `--envelope`. سجّل ما تغيّر ولماذا.

### 6 · الجولة الثانية: تمويل خمس حالات وإيقاف واحدة 30 د

تقرر اللجنة قرارها النهائي: الحالات الممولة، والحالة الموقوفة، وما أُعيد أو أُجّل وشرط عودته. يقرأ المراقبون ملاحظاتهم من `observer_sheet.md` في آخر عشر دقائق.

### ✱ إضافي

أعد القرار لو رُفع السقف الأصلي عشرة في المئة: هل تموّل حالة سادسة، أم تسرّع حالة ممولة؟

## أسئلة تحقق

1. أي حالة كانت سترتفع في الترتيب لو قبلت اللجنة أرقام مالكها كما هي؟
2. هل قرر أحد في اللجنة في حالة يملكها؟
3. ما الذي غيّره المدخلان، وما الذي لم يغيّراه، ولماذا؟
