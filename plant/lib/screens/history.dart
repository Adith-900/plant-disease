import 'package:flutter/material.dart';
import '../models/disease_model.dart';
import '../services/api_service.dart';

class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<DiseaseModel> _history = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() => _isLoading = true);
    final history = await ApiService.getHistory();
    setState(() {
      _history = history;
      _isLoading = false;
    });
  }

  Color _getStatusColor(String diseaseName) {
    if (diseaseName.toLowerCase().contains('healthy')) {
      return Colors.green;
    }
    return Colors.orange;
  }

  IconData _getStatusIcon(String diseaseName) {
    if (diseaseName.toLowerCase().contains('healthy')) {
      return Icons.check_circle;
    }
    return Icons.warning;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Scan History'),
        backgroundColor: Colors.green,
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadHistory,
          ),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _history.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        Icons.history,
                        size: 64,
                        color: Colors.grey.shade400,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'No scan history yet',
                        style: TextStyle(
                          fontSize: 18,
                          color: Colors.grey.shade600,
                        ),
                      ),
                      const SizedBox(height: 8),
                      const Text(
                        'Start by scanning a plant!',
                        style: TextStyle(color: Colors.grey),
                      ),
                    ],
                  ),
                )
              : RefreshIndicator(
                  onRefresh: _loadHistory,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: _history.length,
                    itemBuilder: (context, index) {
                      final item = _history[index];
                      return Card(
                        margin: const EdgeInsets.only(bottom: 12),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: _getStatusColor(item.diseaseName).withOpacity(0.2),
                            child: Icon(
                              _getStatusIcon(item.diseaseName),
                              color: _getStatusColor(item.diseaseName),
                            ),
                          ),
                          title: Text(
                            item.diseaseName,
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Confidence: ${item.confidenceScore.toStringAsFixed(1)}%',
                              ),
                              if (item.timestamp != null)
                                Text(
                                  _formatDate(item.timestamp!),
                                  style: TextStyle(
                                    color: Colors.grey.shade600,
                                    fontSize: 12,
                                  ),
                                ),
                            ],
                          ),
                          trailing: IconButton(
                            icon: const Icon(Icons.info_outline),
                            onPressed: () => _showDetails(item),
                          ),
                        ),
                      );
                    },
                  ),
                ),
    );
  }

  String _formatDate(DateTime date) {
    return '${date.day}/${date.month}/${date.year} ${date.hour}:${date.minute.toString().padLeft(2, '0')}';
  }

  void _showDetails(DiseaseModel item) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(item.diseaseName),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Confidence: ${item.confidenceScore.toStringAsFixed(2)}%'),
            if (item.cropType != null)
              Text('Crop: ${item.cropType}'),
            const SizedBox(height: 16),
            const Text(
              'Remedy:',
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            Text(item.remedy),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}
