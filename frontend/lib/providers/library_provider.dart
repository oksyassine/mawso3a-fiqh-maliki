import 'package:flutter/foundation.dart';
import '../models/book.dart';
import '../services/api_service.dart';
import '../services/local_db.dart';

class LibraryProvider extends ChangeNotifier {
  final ApiService _api = ApiService();
  final LocalDb _localDb = LocalDb();

  List<Book> _books = [];
  List<Book> _mutoon = [];
  Book? _currentBook;
  List<Chapter> _chapters = [];
  List<Passage> _passages = [];
  Chapter? _currentChapter;
  bool _isLoadingBooks = false;
  bool _isLoadingChapters = false;
  bool _isLoadingPassages = false;
  bool _isOffline = false;
  String? _error;
  double _fontSize = 20.0;

  List<Book> get books => _books;
  List<Book> get mutoon => _mutoon;
  Book? get currentBook => _currentBook;
  List<Chapter> get chapters => _chapters;
  List<Passage> get passages => _passages;
  Chapter? get currentChapter => _currentChapter;
  bool get isLoadingBooks => _isLoadingBooks;
  bool get isLoadingChapters => _isLoadingChapters;
  bool get isLoadingPassages => _isLoadingPassages;
  bool get isOffline => _isOffline;
  String? get error => _error;
  double get fontSize => _fontSize;

  void setFontSize(double size) {
    _fontSize = size.clamp(14.0, 36.0);
    notifyListeners();
  }

  Future<void> loadBooks() async {
    _isLoadingBooks = true;
    _error = null;
    notifyListeners();

    try {
      _books = await _api.getBooks();
      _isOffline = false;
    } catch (e) {
      _error = 'تعذر تحميل الكتب';
      _isOffline = true;
    }

    _isLoadingBooks = false;
    notifyListeners();
  }

  Future<void> loadMutoon() async {
    _isLoadingBooks = true;
    _error = null;
    notifyListeners();

    try {
      _mutoon = await _api.getMutoon();
      _isOffline = false;
    } catch (e) {
      _error = 'تعذر تحميل المتون';
      _isOffline = true;
    }

    _isLoadingBooks = false;
    notifyListeners();
  }

  Future<void> selectBook(Book book) async {
    _currentBook = book;
    _chapters = [];
    _passages = [];
    _currentChapter = null;
    notifyListeners();
    await loadChapters(book.id);
  }

  Future<void> loadChapters(int bookId) async {
    _isLoadingChapters = true;
    _error = null;
    notifyListeners();

    try {
      // Try offline first
      final isDownloaded = await _localDb.isBookDownloaded(bookId);
      if (isDownloaded) {
        _chapters = await _localDb.getCachedChapters(bookId);
      } else {
        _chapters = await _api.getChapters(bookId);
      }
      _isOffline = false;
    } catch (e) {
      // Fallback to cache
      try {
        _chapters = await _localDb.getCachedChapters(bookId);
        _isOffline = true;
      } catch (_) {
        _error = 'تعذر تحميل الفهرس';
      }
    }

    if (_chapters.isNotEmpty) {
      _currentChapter = _chapters.first;
      await loadPassages(_chapters.first.id);
    }

    _isLoadingChapters = false;
    notifyListeners();
  }

  Future<void> loadPassages(int chapterId) async {
    _isLoadingPassages = true;
    _error = null;
    notifyListeners();

    _currentChapter = _chapters.where((c) => c.id == chapterId).firstOrNull;

    try {
      // Try offline first
      final cached = await _localDb.getCachedPassages(chapterId);
      if (cached.isNotEmpty) {
        _passages = cached;
      } else if (_currentBook != null) {
        _passages = await _api.getPassages(_currentBook!.id, chapterId);
      }
    } catch (e) {
      try {
        _passages = await _localDb.getCachedPassages(chapterId);
      } catch (_) {
        _error = 'تعذر تحميل النص';
      }
    }

    _isLoadingPassages = false;
    notifyListeners();
  }

  Future<void> goToNextChapter() async {
    if (_currentChapter == null) return;
    final idx = _chapters.indexWhere((c) => c.id == _currentChapter!.id);
    if (idx >= 0 && idx < _chapters.length - 1) {
      await loadPassages(_chapters[idx + 1].id);
    }
  }

  Future<void> goToPreviousChapter() async {
    if (_currentChapter == null) return;
    final idx = _chapters.indexWhere((c) => c.id == _currentChapter!.id);
    if (idx > 0) {
      await loadPassages(_chapters[idx - 1].id);
    }
  }

  bool get hasNextChapter {
    if (_currentChapter == null) return false;
    final idx = _chapters.indexWhere((c) => c.id == _currentChapter!.id);
    return idx >= 0 && idx < _chapters.length - 1;
  }

  bool get hasPreviousChapter {
    if (_currentChapter == null) return false;
    final idx = _chapters.indexWhere((c) => c.id == _currentChapter!.id);
    return idx > 0;
  }
}
