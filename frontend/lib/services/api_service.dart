import 'dart:convert';
import 'package:http/http.dart' as http;
import '../utils/constants.dart';
import '../models/book.dart';
import '../models/taxonomy.dart';
import '../models/comparison.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final http.Client _client = http.Client();
  final String _baseUrl = kApiBaseUrl;

  Future<Map<String, dynamic>> _get(String path,
      {Map<String, String>? queryParams}) async {
    final uri = Uri.parse('$_baseUrl$path').replace(queryParameters: queryParams);
    try {
      final response = await _client.get(uri, headers: {
        'Accept': 'application/json',
      });
      if (response.statusCode == 200) {
        return json.decode(response.body) as Map<String, dynamic>;
      } else {
        throw ApiException(
          'Request failed: ${response.statusCode}',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e', 0);
    }
  }

  Future<List<dynamic>> _getList(String path,
      {Map<String, String>? queryParams}) async {
    final uri = Uri.parse('$_baseUrl$path').replace(queryParameters: queryParams);
    try {
      final response = await _client.get(uri, headers: {
        'Accept': 'application/json',
      });
      if (response.statusCode == 200) {
        return json.decode(response.body) as List<dynamic>;
      } else {
        throw ApiException(
          'Request failed: ${response.statusCode}',
          response.statusCode,
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('Network error: $e', 0);
    }
  }

  // Books
  Future<List<Book>> getBooks() async {
    final data = await _getList('/books');
    return data.map((e) => Book.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<Book>> getMutoon() async {
    final data = await _getList('/books/mutoon');
    return data.map((e) => Book.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<Book> getBook(int id) async {
    final data = await _get('/books/$id');
    return Book.fromJson(data);
  }

  Future<List<Chapter>> getChapters(int bookId) async {
    final data = await _getList('/books/$bookId/chapters');
    return data
        .map((e) => Chapter.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Passage>> getPassages(int bookId, int chapterId) async {
    final data =
        await _getList('/books/$bookId/chapters/$chapterId/passages');
    return data
        .map((e) => Passage.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // Taxonomy
  Future<List<FiqhCategory>> getCategories() async {
    final data = await _getList('/categories');
    return data
        .map((e) => FiqhCategory.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<FiqhCategory> getCategory(int id) async {
    final data = await _get('/categories/$id');
    return FiqhCategory.fromJson(data);
  }

  Future<List<Masala>> getMasail(int categoryId) async {
    final data = await _getList('/categories/$categoryId/masail');
    return data
        .map((e) => Masala.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // Comparisons
  Future<List<Comparison>> getComparisons(int masalaId) async {
    final data = await _getList('/masail/$masalaId/comparisons');
    return data
        .map((e) => Comparison.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  Future<List<Position>> getPositions(int masalaId) async {
    final data = await _getList('/masail/$masalaId/positions');
    return data
        .map((e) => Position.fromJson(e as Map<String, dynamic>))
        .toList();
  }

  // Search
  Future<List<Map<String, dynamic>>> search(String query, {int? bookId}) async {
    final params = <String, String>{'q': query};
    if (bookId != null) params['book_id'] = bookId.toString();
    final data = await _getList('/search', queryParams: params);
    return data.cast<Map<String, dynamic>>();
  }

  void dispose() {
    _client.close();
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;

  ApiException(this.message, this.statusCode);

  @override
  String toString() => 'ApiException($statusCode): $message';
}
