import 'package:flutter/foundation.dart';
import '../models/taxonomy.dart';
import '../services/api_service.dart';

class TaxonomyProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  List<FiqhCategory> _categories = [];
  FiqhCategory? _currentCategory;
  List<Masala> _masail = [];
  bool _isLoadingCategories = false;
  bool _isLoadingMasail = false;
  String? _error;

  List<FiqhCategory> get categories => _categories;
  FiqhCategory? get currentCategory => _currentCategory;
  List<Masala> get masail => _masail;
  bool get isLoadingCategories => _isLoadingCategories;
  bool get isLoadingMasail => _isLoadingMasail;
  String? get error => _error;

  Future<void> loadCategories() async {
    _isLoadingCategories = true;
    _error = null;
    notifyListeners();

    try {
      _categories = await _api.getCategories();
    } catch (e) {
      _error = 'تعذر تحميل الأبواب الفقهية';
    }

    _isLoadingCategories = false;
    notifyListeners();
  }

  Future<void> selectCategory(FiqhCategory category) async {
    _currentCategory = category;
    _masail = [];
    notifyListeners();
    await loadMasail(category.id);
  }

  Future<void> loadMasail(int categoryId) async {
    _isLoadingMasail = true;
    _error = null;
    notifyListeners();

    try {
      _masail = await _api.getMasail(categoryId);
    } catch (e) {
      _error = 'تعذر تحميل المسائل';
    }

    _isLoadingMasail = false;
    notifyListeners();
  }
}
