import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

// Compila con --dart-define=SAMU_URL=https://TU-DOMINIO-HTTPS
const samuUrl = String.fromEnvironment('SAMU_URL', defaultValue: '');

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const SamuApp());
}

class SamuApp extends StatelessWidget {
  const SamuApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SAMU UTGZ',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF28684F)), useMaterial3: true),
      home: (samuUrl.startsWith('https://') ||
        (const bool.fromEnvironment('dart.vm.product') == false &&
         samuUrl.startsWith('http://')))
    ? const SamuWeb()
    : const SetupScreen(),
    );
  }
}

class SetupScreen extends StatelessWidget {
  const SetupScreen({super.key});
  @override
  Widget build(BuildContext context) => const Scaffold(
    body: SafeArea(child: Center(child: Padding(
      padding: EdgeInsets.all(26),
      child: Text('SAMU necesita una URL HTTPS publicada. Compila con --dart-define=SAMU_URL=https://tu-dominio', textAlign: TextAlign.center),
    ))),
  );
}

class SamuWeb extends StatefulWidget {
  const SamuWeb({super.key});
  @override
  State<SamuWeb> createState() => _SamuWebState();
}

class _SamuWebState extends State<SamuWeb> {
  late final WebViewController web;
  bool loading = true;
  @override
  void initState() {
    super.initState();
    web = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setBackgroundColor(const Color(0xFFF3F6F2))
      ..setNavigationDelegate(NavigationDelegate(
        onPageStarted: (_) => setState(() => loading = true),
        onPageFinished: (_) => setState(() => loading = false),
        onNavigationRequest: (request) {
          final link = Uri.tryParse(request.url);
          final origin = Uri.tryParse(samuUrl);
          if (link == null || origin == null) return NavigationDecision.prevent;
          if (link.path.startsWith('/descargar/') ||
              link.path.startsWith('/api/estudiantes/plantilla')) {
            launchUrl(link, mode: LaunchMode.externalApplication);
            return NavigationDecision.prevent;
          }
          if (link.scheme == 'samu') {
            return NavigationDecision.prevent;
          }
          if (link.host != origin.host || link.scheme != 'https') {
            launchUrl(link, mode: LaunchMode.externalApplication);
            return NavigationDecision.prevent;
          }
          return NavigationDecision.navigate;
        },
      ))
      ..loadRequest(Uri.parse(samuUrl).replace(path: '/', query: null, fragment: null));
  }

  Future<bool> goBack() async {
    if (await web.canGoBack()) {
      await web.goBack();
      return false;
    }
    return true;
  }

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: false,
    onPopInvokedWithResult: (didPop, _) async {
  if (didPop) return;

  final shouldExit = await goBack();

  if (!context.mounted) return;

  if (shouldExit) {
    Navigator.of(context).maybePop();
  }
},
    child: Scaffold(
      appBar: AppBar(
        title: const Text('SAMU · UTGZ'),
        backgroundColor: const Color(0xFF28684F),
        foregroundColor: Colors.white,
        actions: [IconButton(tooltip: 'Actualizar', icon: const Icon(Icons.refresh), onPressed: () => web.reload())],
      ),
      body: SafeArea(child: Stack(children: [WebViewWidget(controller: web), if (loading) const LinearProgressIndicator()])),
    ),
  );
}
