import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/disease_model.dart';

class ApiService {
  // URL Configuration:
  // - Windows/Linux/macOS desktop: "http://localhost:8000"
  // - Android Emulator: "http://10.0.2.2:8000"  
  // - Real Android phone: "http://YOUR_PC_IP:8000" (e.g., "http://192.168.1.5:8000")
  // - iOS Simulator: "http://localhost:8000"
  // - Production (Render): Use your Render URL
  static const String baseUrl = "https://plant-disease-api-5i9z.onrender.com";
  
  static String? _authToken;

  // Set auth token after login
  static void setAuthToken(String token) {
    _authToken = token;
  }

  // Clear auth token on logout
  static void clearAuthToken() {
    _authToken = null;
  }

  // Get headers with optional auth
  static Map<String, String> get _headers {
    final headers = {'Content-Type': 'application/json'};
    if (_authToken != null) {
      headers['Authorization'] = 'Bearer $_authToken';
    }
    return headers;
  }

  // Health check
  static Future<bool> checkHealth() async {
    try {
      final response = await http.get(Uri.parse(baseUrl));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  // Register new user
  static Future<Map<String, dynamic>?> register({
    required String email,
    required String password,
    required String fullName,
    String role = 'farmer',
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/register'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'email': email,
          'password': password,
          'full_name': fullName,
          'role': role,
        }),
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print("Registration error: $e");
      return null;
    }
  }

  // Login user
  static Future<String?> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: 'username=$email&password=$password',
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        _authToken = data['access_token'];
        return _authToken;
      }
      return null;
    } catch (e) {
      print("Login error: $e");
      return null;
    }
  }

  // Upload plant image for disease detection
  static Future<DiseaseModel?> uploadPlantImage(File imageFile, {String? cropType}) async {
    try {
      var request = http.MultipartRequest('POST', Uri.parse('$baseUrl/predict'));
      
      // Add auth header if available
      if (_authToken != null) {
        request.headers['Authorization'] = 'Bearer $_authToken';
      }
      
      // Add crop type if provided
      if (cropType != null) {
        request.fields['crop_type'] = cropType;
      }
      
      // Attach the image file to the request
      request.files.add(await http.MultipartFile.fromPath('file', imageFile.path));

      var streamedResponse = await request.send();
      var response = await http.Response.fromStream(streamedResponse);

      if (response.statusCode == 200) {
        final Map<String, dynamic> data = json.decode(response.body);
        return DiseaseModel.fromJson(data);
      } else {
        print("Error: ${response.statusCode}");
        return null;
      }
    } catch (e) {
      print("Exception: $e");
      return null;
    }
  }

  // Get prediction history
  static Future<List<DiseaseModel>> getHistory({int limit = 50}) async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/history?limit=$limit'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => DiseaseModel.fromJson(json)).toList();
      }
      return [];
    } catch (e) {
      print("History error: $e");
      return [];
    }
  }

  // Get analytics
  static Future<Map<String, dynamic>?> getAnalytics() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/analytics'),
        headers: _headers,
      );

      if (response.statusCode == 200) {
        return json.decode(response.body);
      }
      return null;
    } catch (e) {
      print("Analytics error: $e");
      return null;
    }
  }
}