import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';

import 'firebase_options.dart';

final FlutterLocalNotificationsPlugin _localNotifications =
    FlutterLocalNotificationsPlugin();

@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
}

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);

  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);

  const iosInit = DarwinInitializationSettings(
    requestAlertPermission: false,
    requestBadgePermission: false,
    requestSoundPermission: false,
  );
  const initSettings = InitializationSettings(iOS: iosInit);
  await _localNotifications.initialize(initSettings);

  const iosChannel = DarwinNotificationDetails(
    presentAlert: true,
    presentBadge: true,
    presentSound: true,
  );

  FirebaseMessaging.onMessage.listen((message) async {
    final notification = message.notification;
    if (notification == null) return;

    await _localNotifications.show(
      notification.hashCode,
      notification.title,
      notification.body,
      const NotificationDetails(iOS: iosChannel),
    );
  });

  runApp(const MainApp());
}

class MainApp extends StatelessWidget {
  const MainApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: const NotificationsHome(),
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal),
        useMaterial3: true,
      ),
    );
  }
} 

class NotificationsHome extends StatefulWidget {
  const NotificationsHome({super.key});

  @override
  State<NotificationsHome> createState() => _NotificationsHomeState();
}

class _NotificationsHomeState extends State<NotificationsHome> {
  String? _token;
  String _status = 'Not requested';

  @override
  void initState() {
    super.initState();
    _refreshToken();
  }

  Future<void> _refreshToken() async {
    final token = await FirebaseMessaging.instance.getToken();
    if (!mounted) return;
    setState(() => _token = token);
  }

  Future<void> _requestPermission() async {
    setState(() => _status = 'Requesting...');
    final settings = await FirebaseMessaging.instance.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    if (!mounted) return;

    setState(() => _status = settings.authorizationStatus.name);
    await _refreshToken();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('FCM (iOS) setup check')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Permission: $_status'),
            const SizedBox(height: 12),
            FilledButton(
              onPressed: _requestPermission,
              child: const Text('Request notification permission'),
            ),
            const SizedBox(height: 24),
            const Text('FCM token (device)'),
            const SizedBox(height: 8),
            SelectableText(_token ?? '(no token yet)'),
            const Spacer(),
            const Text(
              'Send a test message from Firebase Console to this token.',
            ),
          ],
        ),
      ),
    );
  }
}