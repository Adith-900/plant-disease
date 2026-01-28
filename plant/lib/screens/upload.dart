import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart'; //
import '../models/disease_model.dart'; //

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  File? _image;
  final _picker = ImagePicker();

  // Function to pick image from camera or gallery
  Future<void> _pickImage(ImageSource source) async {
    final pickedFile = await _picker.pickImage(source: source);
    if (pickedFile != null) {
      setState(() {
        _image = File(pickedFile.path);
      });
    }
  }

  // Function to handle the API call and UI feedback
  Future<void> _analyzeImage() async {
    if (_image == null) return;

    // 1. Show Loading Dialog
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => const Center(child: CircularProgressIndicator()),
    );

    // 2. Call the API Service
    final DiseaseModel? result = await ApiService.uploadPlantImage(_image!);

    // 3. Close Loading Dialog
    if (mounted) Navigator.pop(context);

    // 4. Show Result or Error
    if (mounted) {
      if (result != null) {
        _showResultDialog(result);
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text("Failed to analyze image. Check your server connection.")),
        );
      }
    }
  }

  void _showResultDialog(DiseaseModel result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(result.diseaseName, style: const TextStyle(color: Colors.green, fontWeight: FontWeight.bold)),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text("Confidence: ${(result.confidenceScore).toStringAsFixed(2)}%"),
            const SizedBox(height: 10),
            const Text("Suggested Remedy:", style: TextStyle(fontWeight: FontWeight.bold)),
            Text(result.remedy),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text("OK"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text("Plant Disease Detection"),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
      ),
      body: Center(
        child: SingleChildScrollView(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _image != null 
                  ? ClipRRect(
                      borderRadius: BorderRadius.circular(15),
                      child: Image.file(_image!, height: 300, width: 300, fit: BoxFit.cover),
                    ) 
                  : const Icon(Icons.image_search, size: 100, color: Colors.grey),
              const SizedBox(height: 30),
              ElevatedButton.icon(
                onPressed: () => _pickImage(ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: const Text("Take a Photo"),
                style: ElevatedButton.styleFrom(minimumSize: const Size(200, 50)),
              ),
              const SizedBox(height: 10),
              ElevatedButton.icon(
                onPressed: () => _pickImage(ImageSource.gallery),
                icon: const Icon(Icons.photo_library),
                label: const Text("Upload from Gallery"),
                style: ElevatedButton.styleFrom(minimumSize: const Size(200, 50)),
              ),
              if (_image != null)
                Padding(
                  padding: const EdgeInsets.only(top: 30),
                  child: ElevatedButton(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: Colors.green,
                      minimumSize: const Size(250, 60),
                    ),
                    onPressed: _analyzeImage,
                    child: const Text("Analyze Plant", style: TextStyle(color: Colors.white, fontSize: 18)),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}