import 'dart:async';

import 'package:camera/camera.dart';
import 'package:flutter/material.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';

class CameraTextScannerPage extends StatefulWidget {
  const CameraTextScannerPage({super.key});

  @override
  State<CameraTextScannerPage> createState() => _CameraTextScannerPageState();
}

class _CameraTextScannerPageState extends State<CameraTextScannerPage> {
  CameraController? _controller;
  List<CameraDescription> _cameras = const [];

  final TextRecognizer _textRecognizer =
      TextRecognizer(script: TextRecognitionScript.latin);

  bool _isProcessing = false;
  DateTime _lastScan = DateTime.fromMillisecondsSinceEpoch(0);

  // This holds the latest detected text.
  String foundText = '';

  @override
  void initState() {
    super.initState();
    unawaited(_initCamera());
  }

  Future<void> _initCamera() async {
    try {
      _cameras = await availableCameras();
      if (_cameras.isEmpty) return;

      final camera = _cameras.firstWhere(
        (c) => c.lensDirection == CameraLensDirection.back,
        orElse: () => _cameras.first,
      );

      final controller = CameraController(
        camera,
        ResolutionPreset.medium,
        enableAudio: false,
        imageFormatGroup: ImageFormatGroup.yuv420,
      );

      await controller.initialize();
      if (!mounted) {
        await controller.dispose();
        return;
      }

      setState(() => _controller = controller);
      await controller.startImageStream(_processCameraImage);
    } catch (e) {
      // If anything fails (permissions, no camera, etc.), we show it in UI.
      if (!mounted) return;
      setState(() => foundText = 'Camera init failed: $e');
    }
  }

  Future<void> _processCameraImage(CameraImage image) async {
    if (_isProcessing) return;

    // Throttle scans so we don't OCR every frame.
    final now = DateTime.now();
    if (now.difference(_lastScan) < const Duration(milliseconds: 600)) return;
    _lastScan = now;

    _isProcessing = true;
    try {
      final controller = _controller;
      if (controller == null) return;

      final inputImage = _toInputImage(image, controller.description);
      if (inputImage == null) return;

      final recognized = await _textRecognizer.processImage(inputImage);
      final text = recognized.text.trim();

      if (text.isNotEmpty && text != foundText && mounted) {
        setState(() => foundText = text); // <-- saved as a variable/state
      }
    } catch (_) {
      // Ignore per-frame errors.
    } finally {
      _isProcessing = false;
    }
  }

  InputImage? _toInputImage(CameraImage image, CameraDescription description) {
    final controller = _controller;
    if (controller == null) return null;

    // Concatenate planes into a single buffer.
    final bytes = WriteBuffer();
    for (final plane in image.planes) {
      bytes.putUint8List(plane.bytes);
    }
    final buffer = bytes.done().buffer.asUint8List();

    final rotation = InputImageRotationValue.fromRawValue(
      description.sensorOrientation,
    );
    if (rotation == null) return null;

    final format = InputImageFormatValue.fromRawValue(image.format.raw);
    if (format == null) return null;

    final metadata = InputImageMetadata(
      size: Size(image.width.toDouble(), image.height.toDouble()),
      rotation: rotation,
      format: format,
      bytesPerRow: image.planes.first.bytesPerRow,
    );

    return InputImage.fromBytes(bytes: buffer, metadata: metadata);
  }

  @override
  Future<void> dispose() async {
    final controller = _controller;
    _controller = null;
    if (controller != null) {
      try {
        await controller.stopImageStream();
      } catch (_) {}
      await controller.dispose();
    }
    await _textRecognizer.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final controller = _controller;

    return Scaffold(
      appBar: AppBar(title: const Text('Phone Camera Text Scanner')),
      body: Column(
        children: [
          Expanded(
            child: controller == null || !controller.value.isInitialized
                ? const Center(child: CircularProgressIndicator())
                : CameraPreview(controller),
          ),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            color: Colors.black87,
            child: Text(
              foundText.isEmpty ? 'Point at text…' : foundText,
              style: const TextStyle(color: Colors.white),
            ),
          ),
        ],
      ),
    );
  }
}

