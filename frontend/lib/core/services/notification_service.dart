import 'dart:convert';
import 'dart:ui' show Color;
import 'package:flutter/foundation.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:flutter_tts/flutter_tts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../network/api_client.dart';
import '../network/api_endpoints.dart';

/// Top-level handler for background FCM messages.
/// Must be a top-level function (not a class method).
@pragma('vm:entry-point')
Future<void> firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  debugPrint('[FCM] Background message: ${message.messageId}');
  // Show local notification for background messages
  await NotificationService._showLocalNotification(message);
}

/// Push notification service using Firebase Cloud Messaging (FCM).
/// Handles foreground, background, and terminated-state notifications.
class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  final ApiClient _apiClient = ApiClient();
  
  /// Text-to-Speech engine for audio notifications
  final FlutterTts _tts = FlutterTts();
  bool _ttsEnabled = true;
  bool _ttsInitialized = false;

  static const String _fcmTokenKey = 'fcm_token';
  static const String _ttsEnabledKey = 'tts_enabled';

  /// Android notification channel for traffic alerts
  static const AndroidNotificationChannel _channel = AndroidNotificationChannel(
    'itms_traffic_alerts',
    'Traffic Alerts',
    description: 'Notifications for violations, fines, and traffic updates',
    importance: Importance.high,
    playSound: true,
    enableVibration: true,
  );

  /// Callback for handling notification taps in the app
  Function(Map<String, dynamic>)? onNotificationTapped;

  /// Initialize FCM and local notifications
  Future<void> initialize() async {
    // Request permission (iOS & Android 13+)
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
      provisional: false,
      announcement: false,
      carPlay: false,
      criticalAlert: false,
    );

    debugPrint('[FCM] Auth status: ${settings.authorizationStatus}');

    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      debugPrint('[FCM] Notification permission denied');
      return;
    }

    // Create Android notification channel
    await _localNotifications
        .resolvePlatformSpecificImplementation<
            AndroidFlutterLocalNotificationsPlugin>()
        ?.createNotificationChannel(_channel);

    // Initialize local notifications
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    const iosInit = DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );
    await _localNotifications.initialize(
      const InitializationSettings(android: androidInit, iOS: iosInit),
      onDidReceiveNotificationResponse: _onNotificationResponse,
    );

    // Handle foreground messages
    FirebaseMessaging.onMessage.listen(_handleForegroundMessage);

    // Handle notification taps when app is in background
    FirebaseMessaging.onMessageOpenedApp.listen(_handleNotificationTap);

    // Check if app was opened from a terminated state via notification
    final initialMessage = await _messaging.getInitialMessage();
    if (initialMessage != null) {
      _handleNotificationTap(initialMessage);
    }

    // Get and register FCM token
    await _registerToken();

    // Listen for token refresh
    _messaging.onTokenRefresh.listen((newToken) {
      _sendTokenToServer(newToken);
    });
    
    // Initialize TTS
    await _initializeTts();

    debugPrint('[FCM] Notification service initialized');
  }
  
  /// Initialize Text-to-Speech engine
  Future<void> _initializeTts() async {
    try {
      // Load TTS preference
      final prefs = await SharedPreferences.getInstance();
      _ttsEnabled = prefs.getBool(_ttsEnabledKey) ?? true;
      
      // Configure TTS engine
      await _tts.setLanguage('en-US');
      await _tts.setSpeechRate(0.5); // Slower for clarity
      await _tts.setVolume(1.0);
      await _tts.setPitch(1.0);
      
      _ttsInitialized = true;
      debugPrint('[TTS] Text-to-Speech initialized, enabled: $_ttsEnabled');
    } catch (e) {
      debugPrint('[TTS] Failed to initialize TTS: $e');
      _ttsInitialized = false;
    }
  }
  
  /// Enable or disable TTS for notifications
  Future<void> setTtsEnabled(bool enabled) async {
    _ttsEnabled = enabled;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_ttsEnabledKey, enabled);
    debugPrint('[TTS] Audio notifications ${enabled ? "enabled" : "disabled"}');
  }
  
  /// Get current TTS enabled status
  bool get isTtsEnabled => _ttsEnabled;
  
  /// Speak a notification message using TTS
  Future<void> speakNotification(String message) async {
    if (!_ttsEnabled || !_ttsInitialized) return;
    
    try {
      await _tts.stop(); // Stop any ongoing speech
      await _tts.speak(message);
      debugPrint('[TTS] Speaking: $message');
    } catch (e) {
      debugPrint('[TTS] Speak error: $e');
    }
  }
  
  /// Generate a spoken message for a violation notification
  String _generateViolationMessage(Map<String, dynamic> data) {
    final type = data['violation_type'] ?? 'Traffic';
    final fineAmount = data['fine_amount'] ?? '';
    
    // Map violation types to spoken messages
    final typeMessages = {
      'red_light': 'Red light violation detected',
      'speeding': 'Speeding violation detected',
      'parking': 'Parking violation detected',
      'no_parking': 'No parking zone violation',
      'illegal_parking': 'Illegal parking detected',
    };
    
    final spokenType = typeMessages[type.toString().toLowerCase()] ?? 
        '$type violation detected';
    
    if (fineAmount.isNotEmpty && fineAmount != '0') {
      return '$spokenType. Fine amount: $fineAmount rupees.';
    }
    return '$spokenType.';
  }

  /// Get the current FCM token
  Future<String?> getToken() async {
    try {
      return await _messaging.getToken();
    } catch (e) {
      debugPrint('[FCM] Token error: $e');
      return null;
    }
  }

  /// Register FCM token with the backend
  Future<void> _registerToken() async {
    try {
      final token = await _messaging.getToken();
      if (token == null) return;

      // Check if token changed
      final prefs = await SharedPreferences.getInstance();
      final storedToken = prefs.getString(_fcmTokenKey);
      if (storedToken == token) return;

      await _sendTokenToServer(token);
      await prefs.setString(_fcmTokenKey, token);
    } catch (e) {
      debugPrint('[FCM] Token registration error: $e');
    }
  }

  /// Send FCM token to backend
  Future<void> _sendTokenToServer(String token) async {
    try {
      await _apiClient.post(
        ApiEndpoints.registerFcmToken,
        body: {'fcm_token': token, 'platform': defaultTargetPlatform.name},
      );
      debugPrint('[FCM] Token sent to server');
    } catch (e) {
      debugPrint('[FCM] Send token error: $e');
    }
  }

  /// Handle foreground messages - show local notification and speak if violation
  void _handleForegroundMessage(RemoteMessage message) {
    debugPrint('[FCM] Foreground message: ${message.notification?.title}');
    _showLocalNotification(message);
    
    // Speak violation notifications using TTS
    final data = message.data;
    if (data['type'] == 'violation') {
      final spokenMessage = _generateViolationMessage(data);
      speakNotification(spokenMessage);
    } else if (data['type'] == 'fine') {
      final amount = data['amount'] ?? '';
      speakNotification('Fine issued. Amount: $amount rupees.');
    } else if (message.notification?.body != null) {
      // For other notification types, speak the body
      speakNotification(message.notification!.body!);
    }
  }

  /// Handle notification tap (app in background/terminated)
  void _handleNotificationTap(RemoteMessage message) {
    debugPrint('[FCM] Notification tapped: ${message.data}');
    onNotificationTapped?.call(message.data);
  }

  /// Handle tap on local notification
  void _onNotificationResponse(NotificationResponse response) {
    if (response.payload != null) {
      try {
        final data = jsonDecode(response.payload!) as Map<String, dynamic>;
        onNotificationTapped?.call(data);
      } catch (_) {}
    }
  }

  /// Show a local notification from RemoteMessage
  static Future<void> _showLocalNotification(RemoteMessage message) async {
    final notification = message.notification;
    final android = message.notification?.android;

    final localNotif = FlutterLocalNotificationsPlugin();

    // Initialize (needed for background handler)
    const androidInit = AndroidInitializationSettings('@mipmap/ic_launcher');
    await localNotif.initialize(
      const InitializationSettings(android: androidInit),
    );

    if (notification != null) {
      await localNotif.show(
        notification.hashCode,
        notification.title ?? 'Traffic Alert',
        notification.body ?? '',
        NotificationDetails(
          android: AndroidNotificationDetails(
            _channel.id,
            _channel.name,
            channelDescription: _channel.description,
            importance: Importance.high,
            priority: Priority.high,
            icon: android?.smallIcon ?? '@mipmap/ic_launcher',
            color: const Color(0xFFFFD700),
          ),
          iOS: const DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        payload: jsonEncode(message.data),
      );
    }
  }

  /// Subscribe to a topic (e.g., junction-specific alerts)
  Future<void> subscribeToTopic(String topic) async {
    try {
      await _messaging.subscribeToTopic(topic);
      debugPrint('[FCM] Subscribed to topic: $topic');
    } catch (e) {
      debugPrint('[FCM] Subscribe error: $e');
    }
  }

  /// Unsubscribe from a topic
  Future<void> unsubscribeFromTopic(String topic) async {
    try {
      await _messaging.unsubscribeFromTopic(topic);
      debugPrint('[FCM] Unsubscribed from topic: $topic');
    } catch (e) {
      debugPrint('[FCM] Unsubscribe error: $e');
    }
  }

  /// Clear stored token (on logout)
  Future<void> clearToken() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_fcmTokenKey);
      await _messaging.deleteToken();
      debugPrint('[FCM] Token cleared');
    } catch (e) {
      debugPrint('[FCM] Clear token error: $e');
    }
  }
}
