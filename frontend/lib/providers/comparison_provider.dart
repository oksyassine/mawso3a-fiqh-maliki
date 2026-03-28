import 'package:flutter/foundation.dart';
import '../models/comparison.dart';
import '../services/api_service.dart';

class ComparisonProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<Comparison> _comparisons = [];
  List<Position> _positions = [];
  bool _isLoadingComparisons = false;
  bool _isLoadingPositions = false;
  String? _error;

  List<Comparison> get comparisons => _comparisons;
  List<Position> get positions => _positions;
  bool get isLoadingComparisons => _isLoadingComparisons;
  bool get isLoadingPositions => _isLoadingPositions;
  String? get error => _error;

  Future<void> loadComparisons(int masalaId) async {
    _isLoadingComparisons = true;
    _error = null;
    notifyListeners();

    try {
      _comparisons = await _api.getComparisons(masalaId);
    } catch (e) {
      _error = 'تعذر تحميل المقارنات';
    }

    _isLoadingComparisons = false;
    notifyListeners();
  }

  Future<void> loadPositions(int masalaId) async {
    _isLoadingPositions = true;
    _error = null;
    notifyListeners();

    try {
      _positions = await _api.getPositions(masalaId);
    } catch (e) {
      _error = 'تعذر تحميل الأقوال';
    }

    _isLoadingPositions = false;
    notifyListeners();
  }
}
