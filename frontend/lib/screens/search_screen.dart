import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../providers/library_provider.dart';
import '../models/book.dart';
import '../utils/theme.dart';
import '../widgets/arabic_text.dart';
import 'book_reader_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ApiService _api = ApiService();
  List<Map<String, dynamic>> _results = [];
  bool _isSearching = false;
  String? _error;
  int? _selectedBookId;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _search() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) return;

    setState(() {
      _isSearching = true;
      _error = null;
    });

    try {
      _results = await _api.search(query, bookId: _selectedBookId);
    } catch (e) {
      _error = 'تعذر البحث';
      _results = [];
    }

    setState(() => _isSearching = false);
  }

  @override
  Widget build(BuildContext context) {
    final books = context.watch<LibraryProvider>().books;

    return Column(
      children: [
        // Search bar
        Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              TextField(
                controller: _searchController,
                textDirection: TextDirection.rtl,
                textAlign: TextAlign.right,
                style: AppTheme.arabicBody(fontSize: 16, color: AppColors.cream),
                decoration: InputDecoration(
                  hintText: 'ابحث في النصوص...',
                  hintTextDirection: TextDirection.rtl,
                  prefixIcon: const Icon(Icons.search, color: AppColors.creamDim),
                  suffixIcon: _searchController.text.isNotEmpty
                      ? IconButton(
                          icon: const Icon(Icons.clear,
                              color: AppColors.creamDim),
                          onPressed: () {
                            _searchController.clear();
                            setState(() {
                              _results = [];
                              _error = null;
                            });
                          },
                        )
                      : null,
                ),
                onSubmitted: (_) => _search(),
                onChanged: (_) => setState(() {}),
              ),
              const SizedBox(height: 8),
              // Book filter
              if (books.isNotEmpty)
                SizedBox(
                  height: 40,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    reverse: true,
                    children: [
                      Padding(
                        padding: const EdgeInsets.only(left: 8),
                        child: FilterChip(
                          label: const Text('الكل'),
                          selected: _selectedBookId == null,
                          onSelected: (_) {
                            setState(() => _selectedBookId = null);
                            if (_searchController.text.isNotEmpty) _search();
                          },
                          selectedColor: AppColors.gold,
                          labelStyle: AppTheme.arabicCaption(
                            color: _selectedBookId == null
                                ? AppColors.background
                                : AppColors.cream,
                          ),
                        ),
                      ),
                      ...books.map((book) => Padding(
                            padding: const EdgeInsets.only(left: 8),
                            child: FilterChip(
                              label: Text(book.shortTitleAr ?? book.titleAr),
                              selected: _selectedBookId == book.id,
                              onSelected: (_) {
                                setState(() => _selectedBookId = book.id);
                                if (_searchController.text.isNotEmpty) {
                                  _search();
                                }
                              },
                              selectedColor: AppColors.gold,
                              labelStyle: AppTheme.arabicCaption(
                                color: _selectedBookId == book.id
                                    ? AppColors.background
                                    : AppColors.cream,
                              ),
                            ),
                          )),
                    ],
                  ),
                ),
            ],
          ),
        ),
        const Divider(height: 1),
        // Results
        Expanded(
          child: _isSearching
              ? const Center(
                  child: CircularProgressIndicator(color: AppColors.gold),
                )
              : _error != null
                  ? Center(
                      child: ArabicText(_error!, color: AppColors.creamDim),
                    )
                  : _results.isEmpty
                      ? Center(
                          child: _searchController.text.isEmpty
                              ? Column(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    Icon(Icons.search,
                                        size: 64,
                                        color:
                                            AppColors.gold.withValues(alpha: 0.3)),
                                    const SizedBox(height: 16),
                                    const ArabicText(
                                      'ابحث في نصوص الكتب',
                                      color: AppColors.creamDim,
                                    ),
                                  ],
                                )
                              : const ArabicText(
                                  'لا توجد نتائج',
                                  color: AppColors.creamDim,
                                ),
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.symmetric(vertical: 8),
                          itemCount: _results.length,
                          separatorBuilder: (_, index2) =>
                              const Divider(height: 1, indent: 16, endIndent: 16),
                          itemBuilder: (context, index) {
                            return _buildResultTile(_results[index]);
                          },
                        ),
        ),
      ],
    );
  }

  Widget _buildResultTile(Map<String, dynamic> result) {
    final text = result['text_ar'] as String? ?? '';
    final bookTitle = result['book_title_ar'] as String? ?? '';
    final chapterTitle = result['chapter_title_ar'] as String? ?? '';
    final query = _searchController.text.trim();

    // Highlight matching text
    final snippet = _getSnippet(text, query, maxLen: 200);

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      title: RichText(
        textDirection: TextDirection.rtl,
        textAlign: TextAlign.right,
        text: _highlightText(snippet, query),
      ),
      subtitle: Padding(
        padding: const EdgeInsets.only(top: 6),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.end,
          children: [
            if (chapterTitle.isNotEmpty)
              Flexible(
                child: Text(
                  chapterTitle,
                  style: AppTheme.arabicCaption(fontSize: 12),
                  textDirection: TextDirection.rtl,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            if (chapterTitle.isNotEmpty && bookTitle.isNotEmpty)
              Text(' - ',
                  style: AppTheme.arabicCaption(
                      fontSize: 12, color: AppColors.creamDim)),
            if (bookTitle.isNotEmpty)
              Text(
                bookTitle,
                style: AppTheme.arabicCaption(
                    fontSize: 12, color: AppColors.goldLight),
                textDirection: TextDirection.rtl,
              ),
          ],
        ),
      ),
      onTap: () {
        final bookId = result['book_id'] as int?;
        if (bookId != null) {
          final book = Book(
            id: bookId,
            titleAr: bookTitle,
            textType: 'matn',
          );
          context.read<LibraryProvider>().selectBook(book);
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => BookReaderScreen(book: book),
            ),
          );
        }
      },
    );
  }

  String _getSnippet(String text, String query, {int maxLen = 200}) {
    if (text.length <= maxLen) return text;
    final idx = text.indexOf(query);
    if (idx < 0) return '${text.substring(0, maxLen)}...';
    final start = (idx - maxLen ~/ 2).clamp(0, text.length);
    final end = (start + maxLen).clamp(0, text.length);
    final prefix = start > 0 ? '...' : '';
    final suffix = end < text.length ? '...' : '';
    return '$prefix${text.substring(start, end)}$suffix';
  }

  TextSpan _highlightText(String text, String query) {
    if (query.isEmpty) {
      return TextSpan(
        text: text,
        style: AppTheme.arabicBody(fontSize: 15, color: AppColors.cream),
      );
    }

    final spans = <TextSpan>[];
    final lowerText = text.toLowerCase();
    final lowerQuery = query.toLowerCase();
    int start = 0;

    while (true) {
      final idx = lowerText.indexOf(lowerQuery, start);
      if (idx < 0) {
        spans.add(TextSpan(
          text: text.substring(start),
          style: AppTheme.arabicBody(fontSize: 15, color: AppColors.cream),
        ));
        break;
      }
      if (idx > start) {
        spans.add(TextSpan(
          text: text.substring(start, idx),
          style: AppTheme.arabicBody(fontSize: 15, color: AppColors.cream),
        ));
      }
      spans.add(TextSpan(
        text: text.substring(idx, idx + query.length),
        style: AppTheme.arabicBody(fontSize: 15, color: AppColors.gold)
            .copyWith(backgroundColor: AppColors.gold.withValues(alpha: 0.2)),
      ));
      start = idx + query.length;
    }

    return TextSpan(children: spans);
  }
}
