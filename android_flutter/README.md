# Android (Flutter) - SAMU

El código Flutter es un contenedor Android de la misma interfaz segura PWA: no necesita Expo Go ni aplicaciones auxiliares para el usuario final. La conexión a Internet es necesaria para consultar o enviar fichas.

## Compilación por la persona desarrolladora
1. Instalar Flutter SDK y Android SDK en la computadora de desarrollo (solo una vez). Verificar `flutter doctor`.
2. Abrir terminal dentro de `android_flutter` y ejecutar `flutter create . --platforms=android` para generar carpetas Android nativas. **No sobrescribas** `lib/main.dart` ni `pubspec.yaml` (si Flutter te pregunta o los altera, restáuralos).
3. `flutter pub get`.
4. En `android/app/src/main/AndroidManifest.xml` comprobar que exista `<uses-permission android:name="android.permission.INTERNET" />` dentro de `<manifest>`; Flutter suele incluirla en el manifest de desarrollo, no en el de producción.
5. Publicar primero SAMU en un dominio HTTPS real.
6. `flutter build apk --release --dart-define=SAMU_URL=https://tu-dominio.edu.mx`.
7. APK en `build/app/outputs/flutter-apk/app-release.apk`.

**No se entrega APK precompilado**: Flutter/Android SDK no está instalado en el entorno de generación de este paquete. Las notificaciones, descarga de PDFs y firma deben validarse en dispositivos Android reales antes de distribución.
