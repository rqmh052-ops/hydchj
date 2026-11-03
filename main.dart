import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:url_launcher/url_launcher.dart';

const bg = Color(0xFF090D14), surface = Color(0xFF0F1624), border = Color(0xFF1E2A40);
const textC = Color(0xFFE8EEF8), muted = Color(0xFF8FA0BC), blue = Color(0xFF4D8BFF), cyan = Color(0xFF6FD3E8);
const channels = ['https://t.me/Bayan_x777', 'https://youtube.com/channel/UC4Ox1C-_DWCbIeiWJ_6rV9Q'];
const native = MethodChannel('pyvault/protect');

void main() => runApp(const PyVaultApp());

class PyVaultApp extends StatefulWidget {
  const PyVaultApp({super.key});
  @override State<PyVaultApp> createState() => _PyVaultAppState();
}
class _PyVaultAppState extends State<PyVaultApp> {
  bool english = false, busy = false;
  PlatformFile? picked;
  Uint8List? pickedBytes;
  int pickedSize = 0;
  String status = '';
  String tr(String ar, String en) => english ? en : ar;
  Future<void> chooseFile() async {
    try {
      final f = await FilePicker.pickFile(type: FileType.custom, allowedExtensions: ['py']);
      if (f == null) return;
      if (!f.name.toLowerCase().endsWith('.py')) throw Exception(tr('اختر ملف Python بامتداد .py','Select a Python .py file'));
      final size = await f.length();
      if (size == null) throw Exception(tr('تعذر التحقق من حجم الملف. اختر ملفاً محلياً يمكن قراءته.','Could not verify the file size. Choose a readable local file.'));
      if (size > 32 * 1024 * 1024) throw Exception(tr('الحد الأقصى المدعوم 32 ميجابايت','Maximum supported size is 32 MB'));
      final bytes = await f.readAsBytes();
      if (bytes.length > 32 * 1024 * 1024) throw Exception(tr('الحد الأقصى المدعوم 32 ميجابايت','Maximum supported size is 32 MB'));
      setState(() { picked = f; pickedBytes = bytes; pickedSize = bytes.length; status = ''; });
    } catch (e) { setState(() => status = e.toString().replaceFirst('Exception: ', '')); }
  }
  Future<void> protect() async {
    final f = picked;
    final sourceBytes = pickedBytes;
    if (f == null || sourceBytes == null || busy) return;
    setState(() { busy = true; status = tr('يجري تجهيز الملف محلياً…','Protecting locally…'); });
    try {
      final Uint8List? output = await native.invokeMethod<Uint8List>('protectBytes', {'name': f.name, 'bytes': sourceBytes});
      // invokeMethod returns nullable; a null here means the native side produced nothing, so fail loudly instead of saving an empty file.
      if (output == null) throw Exception(tr('فشلت المعالجة: لم يُرجع المحرك أي ناتج.','Protection failed: the engine returned no output.'));
      final base = f.name.replaceAll(RegExp(r'\.py$', caseSensitive: false), '');
      final saved = await FilePicker.saveFile(fileName: '${base}_protected.py', bytes: output, mimeType: 'text/x-python');
      setState(() => status = saved == null ? tr('أُلغي الحفظ؛ لم يُرسل الملف لأي جهة.','Save cancelled; no file was sent anywhere.') : tr('تم إنشاء وحفظ الملف المحمي.','Protected file created and saved.'));
    } on PlatformException catch (e) {
      setState(() => status = e.message ?? e.code);
    } catch (e) { setState(() => status = e.toString()); }
    finally { if (mounted) setState(() => busy = false); }
  }
  Widget card(Widget child) => Container(padding: const EdgeInsets.all(18), decoration: BoxDecoration(color: surface, border: Border.all(color: border), borderRadius: BorderRadius.circular(18)), child: child);
  @override Widget build(BuildContext context) {
    final isRtl = !english;
    return MaterialApp(debugShowCheckedModeBanner: false, theme: ThemeData(useMaterial3: true, brightness: Brightness.dark, fontFamily: 'Tajawal', scaffoldBackgroundColor: bg, colorScheme: const ColorScheme.dark(primary: blue, secondary: cyan, surface: surface)), home: Directionality(textDirection: isRtl ? TextDirection.rtl : TextDirection.ltr, child: Scaffold(
      appBar: AppBar(backgroundColor: bg, title: Text('PyVault', style: const TextStyle(fontWeight: FontWeight.w800)), actions: [Builder(builder: (context) => IconButton(onPressed: () => Scaffold.of(context).openEndDrawer(), icon: const Icon(Icons.menu_rounded))) ]),
      endDrawer: Drawer(backgroundColor: surface, width: 300, child: SafeArea(child: Padding(padding: const EdgeInsets.all(18), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        const Padding(padding: EdgeInsets.fromLTRB(6,16,6,24), child: Text('PyVault', style: TextStyle(fontSize: 22,fontWeight: FontWeight.w800,color: textC))),
        ListTile(leading: const Icon(Icons.translate,color: cyan), title: Text(tr('اللغة','Language')), subtitle: Text(english?'English':'العربية'), onTap: () { setState(() => english=!english); Navigator.pop(context); }),
        const Divider(color: border),
        ListTile(leading: const Icon(Icons.send_rounded,color: blue), title: Text(tr('القناة الأولى','Channel 1')), onTap: () { Navigator.pop(context); launchUrl(Uri.parse(channels[0]),mode: LaunchMode.externalApplication); }),
        ListTile(leading: const Icon(Icons.play_circle_outline,color: blue), title: Text(tr('القناة الثانية','Channel 2')), onTap: () { Navigator.pop(context); launchUrl(Uri.parse(channels[1]),mode: LaunchMode.externalApplication); }),
        ListTile(leading: const Icon(Icons.folder_open,color: cyan), title: Text(tr('الصلاحيات','Permissions')), onTap: () { Navigator.pop(context); showDialog(context: context,builder: (_) => AlertDialog(backgroundColor: surface,title: Text(tr('الوصول إلى الملفات','File access')),content: Text(tr('يستخدم التطبيق نافذة اختيار الملفات النظامية لمنح وصول محدود للملف الذي تختاره فقط. لا يطلب صلاحية تخزين عامة أو أي صلاحية أخرى.','The app uses Android’s system file picker for access only to files you select. It requests no broad storage permission or other permission.')),actions: [TextButton(onPressed: () => Navigator.pop(context),child: Text(tr('حسناً','OK')))])); }),
        const Spacer(), const Text('Offline • AES-256-GCM',style: TextStyle(color: muted,fontSize:12)),
      ])))),
      body: SafeArea(child: SingleChildScrollView(padding: const EdgeInsets.all(20), child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Container(height: 160, decoration: BoxDecoration(borderRadius: BorderRadius.circular(24), gradient: const LinearGradient(colors: [Color(0xFF142A50),Color(0xFF101827),Color(0xFF0D2231)], begin: Alignment.topLeft,end: Alignment.bottomRight), border: Border.all(color: const Color(0xFF24436C))), child: Stack(children: [Positioned(right: 18,top: 14,child: Icon(Icons.shield_moon_outlined,size: 100,color: cyan.withValues(alpha:.14))), Padding(padding: const EdgeInsets.all(22),child: Column(crossAxisAlignment: CrossAxisAlignment.start,mainAxisAlignment: MainAxisAlignment.center,children: [const Icon(Icons.lock_outline_rounded,color: cyan,size:28),const SizedBox(height:12),Text(tr('حماية سكربتات Python','Protect Python scripts'),style: const TextStyle(fontSize:21,fontWeight:FontWeight.w800)),const SizedBox(height:4),Text(tr('معالجة محلية على جهازك — بلا حساب أو رفع','Local processing — no account, no uploads'),style: const TextStyle(color:muted,fontSize:13))]))])),
        const SizedBox(height:22), Text(tr('ملف المصدر','Source file'),style: const TextStyle(color:muted,fontWeight:FontWeight.w700)),const SizedBox(height:9),
        InkWell(onTap: busy?null:chooseFile, borderRadius: BorderRadius.circular(16), child: card(Row(children: [const Icon(Icons.description_outlined,color:blue,size:28),const SizedBox(width:12),Expanded(child: Column(crossAxisAlignment:CrossAxisAlignment.start,children: [Text(picked?.name ?? tr('اختر ملف .py','Choose a .py file'),style: const TextStyle(fontWeight:FontWeight.w700)),const SizedBox(height:4),Text(picked==null?tr('حتى 32 ميجابايت','Up to 32 MB'):'${(pickedSize/1024).toStringAsFixed(1)} KB',style: const TextStyle(color:muted,fontSize:12))])),const Icon(Icons.folder_open,color:cyan)]))),
        const SizedBox(height:16), card(Column(crossAxisAlignment:CrossAxisAlignment.start,children: [Row(children:[const Icon(Icons.verified_user_outlined,color:cyan),const SizedBox(width:8),Text(tr('الحماية المفعّلة','Protection enabled'),style:const TextStyle(fontWeight:FontWeight.w800))]),const SizedBox(height:12),_line(tr('AES-256-GCM مع تحقق سلامة مدمج','AES-256-GCM authenticated encryption'),Icons.lock),_line(tr('ضغط ثم تجميع bytecode خاص بإصدار Python','Compression and version-bound Python bytecode'),Icons.code),_line(tr('لا شبكة ولا مفاتيح يطلبها التطبيق','No network or user-entered key'),Icons.wifi_off)])),
        const SizedBox(height:18), SizedBox(height:54,child:FilledButton.icon(onPressed: picked==null||busy?null:protect,icon:busy?const SizedBox(width:18,height:18,child:CircularProgressIndicator(strokeWidth:2)):const Icon(Icons.bolt_rounded),label:Text(tr('تشفير الآن','Protect now'),style:const TextStyle(fontWeight:FontWeight.w800,fontSize:16)),style:FilledButton.styleFrom(backgroundColor:blue,foregroundColor:Colors.white,shape:RoundedRectangleBorder(borderRadius:BorderRadius.circular(14))))),
        if(status.isNotEmpty) ...[const SizedBox(height:14),card(Text(status,style:TextStyle(color:status.contains('تم')||status.contains('created')?const Color(0xFF5BD68A):textC)))],
        const SizedBox(height:20), Text(tr('ملاحظة توافق: الملف الناتج يحتاج CPython بنفس الإصدار الدقيق ومكتبة cryptography. لا يشغّل Android ملفات Python تلقائياً دون بيئة Python.','Compatibility: output requires the exact same CPython minor version and cryptography. Android does not run .py files without a Python runtime.'),style:const TextStyle(color:muted,fontSize:12,height:1.5)),
      ]))),
    )));
  }
  Widget _line(String label, IconData icon) => Padding(padding: const EdgeInsets.only(top:10),child: Row(children:[Icon(icon,size:16,color:muted),const SizedBox(width:9),Expanded(child:Text(label,style:const TextStyle(color:textC,fontSize:13)))]));
}
