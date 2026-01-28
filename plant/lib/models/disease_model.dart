class DiseaseModel {
  final int? id;
  final String diseaseName;
  final String remedy;
  final double confidenceScore;
  final String? cropType;
  final DateTime? timestamp;

  DiseaseModel({
    this.id,
    required this.diseaseName,
    required this.remedy,
    required this.confidenceScore,
    this.cropType,
    this.timestamp,
  });

  /// Converts FastAPI JSON response into DiseaseModel object
  factory DiseaseModel.fromJson(Map<String, dynamic> json) {
    return DiseaseModel(
      id: json['id'],
      diseaseName: json['disease_name'] ?? 'Unknown Disease',
      remedy: json['remedy'] ?? 'No remedy available',
      confidenceScore: (json['confidence'] as num?)?.toDouble() ?? 0.0,
      cropType: json['crop_type'],
      timestamp: json['timestamp'] != null 
          ? DateTime.parse(json['timestamp']) 
          : null,
    );
  }

  @override
  String toString() {
    return 'DiseaseModel(diseaseName: $diseaseName, confidenceScore: $confidenceScore, remedy: $remedy)';
  }
}
