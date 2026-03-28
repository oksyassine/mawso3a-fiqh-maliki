import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/book.dart';
import '../providers/library_provider.dart';
import '../services/local_db.dart';
import '../utils/theme.dart';
import '../widgets/arabic_text.dart';

class BookReaderScreen extends StatefulWidget {
  final Book book;
  final Book? sharhBook;

  const BookReaderScreen({super.key, required this.book, this.sharhBook});

  @override
  State<BookReaderScreen> createState() => _BookReaderScreenState();
}

class _BookReaderScreenState extends State<BookReaderScreen> {
  bool _showSharh = false;
  bool _isBookmarked = false;
  final ScrollController _scrollController = ScrollController();
  final LocalDb _localDb = LocalDb();

  @override
  void initState() {
    super.initState();
    _checkBookmark();
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _checkBookmark() async {
    final provider = context.read<LibraryProvider>();
    if (provider.currentChapter != null) {
      final marked =
          await _localDb.isBookmarked(provider.currentChapter!.id);
      if (mounted) setState(() => _isBookmarked = marked);
    }
  }

  Future<void> _toggleBookmark() async {
    final provider = context.read<LibraryProvider>();
    if (provider.currentChapter == null) return;

    if (_isBookmarked) {
      final bookmarks =
          await _localDb.getBookmarks(bookId: widget.book.id);
      for (final bm in bookmarks) {
        if (bm['chapter_id'] == provider.currentChapter!.id) {
          await _localDb.removeBookmark(bm['id'] as int);
        }
      }
    } else {
      await _localDb.addBookmark(
        bookId: widget.book.id,
        chapterId: provider.currentChapter!.id,
      );
    }

    setState(() => _isBookmarked = !_isBookmarked);
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<LibraryProvider>(
      builder: (context, provider, _) {
        return Scaffold(
          appBar: AppBar(
            title: Text(
              widget.book.shortTitleAr ?? widget.book.titleAr,
              style: AppTheme.arabicTitle(fontSize: 18),
              overflow: TextOverflow.ellipsis,
            ),
            actions: [
              if (widget.book.commentaries != null &&
                  widget.book.commentaries!.isNotEmpty)
                IconButton(
                  icon: Icon(
                    _showSharh ? Icons.vertical_split : Icons.subject,
                    color: _showSharh ? AppColors.gold : AppColors.creamDim,
                  ),
                  tooltip: 'عرض الشرح',
                  onPressed: () => setState(() => _showSharh = !_showSharh),
                ),
            ],
          ),
          drawer: _buildChapterDrawer(provider),
          body: GestureDetector(
            onHorizontalDragEnd: (details) {
              if (details.primaryVelocity == null) return;
              // Swipe right (RTL: next chapter)
              if (details.primaryVelocity! > 200 && provider.hasNextChapter) {
                provider.goToNextChapter();
                _scrollController.jumpTo(0);
              }
              // Swipe left (RTL: previous chapter)
              if (details.primaryVelocity! < -200 &&
                  provider.hasPreviousChapter) {
                provider.goToPreviousChapter();
                _scrollController.jumpTo(0);
              }
            },
            child: _showSharh
                ? _buildSplitView(provider)
                : _buildSingleView(provider),
          ),
          bottomNavigationBar: _buildBottomBar(provider),
        );
      },
    );
  }

  Widget _buildChapterDrawer(LibraryProvider provider) {
    return Drawer(
      backgroundColor: AppColors.background,
      child: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              color: AppColors.surface,
              child: ArabicText(
                'فهرس الكتاب',
                fontSize: 20,
                color: AppColors.gold,
                fontWeight: FontWeight.bold,
                textAlign: TextAlign.center,
              ),
            ),
            const Divider(height: 1),
            if (provider.isLoadingChapters)
              const Expanded(
                child: Center(
                  child: CircularProgressIndicator(color: AppColors.gold),
                ),
              )
            else
              Expanded(
                child: ListView.builder(
                  itemCount: provider.chapters.length,
                  itemBuilder: (context, index) {
                    final chapter = provider.chapters[index];
                    final isSelected =
                        provider.currentChapter?.id == chapter.id;
                    return ListTile(
                      tileColor:
                          isSelected ? AppColors.surfaceLight : null,
                      title: Text(
                        chapter.titleAr,
                        style: AppTheme.arabicBody(
                          fontSize: 16,
                          color:
                              isSelected ? AppColors.gold : AppColors.cream,
                        ),
                        textDirection: TextDirection.rtl,
                      ),
                      onTap: () {
                        provider.loadPassages(chapter.id);
                        _scrollController.jumpTo(0);
                        Navigator.pop(context);
                      },
                    );
                  },
                ),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildSingleView(LibraryProvider provider) {
    if (provider.isLoadingPassages) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.gold),
      );
    }

    if (provider.passages.isEmpty) {
      return const Center(
        child: ArabicText('لا يوجد نص', color: AppColors.creamDim),
      );
    }

    return ListView.builder(
      controller: _scrollController,
      padding: const EdgeInsets.all(20),
      itemCount: provider.passages.length,
      itemBuilder: (context, index) {
        final passage = provider.passages[index];
        return Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Text(
            passage.textAr,
            textDirection: TextDirection.rtl,
            textAlign: TextAlign.justify,
            style: AppTheme.arabicBody(
              fontSize: provider.fontSize,
              color: AppColors.cream,
            ),
          ),
        );
      },
    );
  }

  Widget _buildSplitView(LibraryProvider provider) {
    if (provider.isLoadingPassages) {
      return const Center(
        child: CircularProgressIndicator(color: AppColors.gold),
      );
    }

    return Column(
      children: [
        // Matn (top)
        Expanded(
          child: Container(
            decoration: const BoxDecoration(
              border: Border(
                bottom: BorderSide(color: AppColors.gold, width: 2),
              ),
            ),
            child: ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: provider.passages.length,
              itemBuilder: (context, index) {
                final passage = provider.passages[index];
                return Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: Text(
                    passage.textAr,
                    textDirection: TextDirection.rtl,
                    textAlign: TextAlign.justify,
                    style: AppTheme.arabicBody(
                      fontSize: provider.fontSize,
                      color: AppColors.cream,
                    ),
                  ),
                );
              },
            ),
          ),
        ),
        // Sharh (bottom)
        Expanded(
          child: Container(
            color: AppColors.surfaceLight,
            child: const Center(
              child: ArabicText(
                'الشرح غير متوفر حاليا',
                color: AppColors.creamDim,
              ),
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildBottomBar(LibraryProvider provider) {
    return Container(
      color: AppColors.surface,
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      child: SafeArea(
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            // Font size decrease
            IconButton(
              icon: const Icon(Icons.text_decrease, color: AppColors.creamDim),
              onPressed: () => provider.setFontSize(provider.fontSize - 2),
            ),
            // Font size display
            Text(
              '${provider.fontSize.toInt()}',
              style: AppTheme.arabicCaption(color: AppColors.creamDim),
            ),
            // Font size increase
            IconButton(
              icon: const Icon(Icons.text_increase, color: AppColors.creamDim),
              onPressed: () => provider.setFontSize(provider.fontSize + 2),
            ),
            const VerticalDivider(
              width: 24,
              thickness: 1,
              color: AppColors.divider,
            ),
            // Bookmark
            IconButton(
              icon: Icon(
                _isBookmarked ? Icons.bookmark : Icons.bookmark_border,
                color: _isBookmarked ? AppColors.gold : AppColors.creamDim,
              ),
              onPressed: _toggleBookmark,
            ),
            // Chapter navigation
            IconButton(
              icon: const Icon(Icons.arrow_forward),
              color: provider.hasPreviousChapter
                  ? AppColors.gold
                  : AppColors.divider,
              onPressed: provider.hasPreviousChapter
                  ? () {
                      provider.goToPreviousChapter();
                      _scrollController.jumpTo(0);
                    }
                  : null,
            ),
            IconButton(
              icon: const Icon(Icons.arrow_back),
              color:
                  provider.hasNextChapter ? AppColors.gold : AppColors.divider,
              onPressed: provider.hasNextChapter
                  ? () {
                      provider.goToNextChapter();
                      _scrollController.jumpTo(0);
                    }
                  : null,
            ),
          ],
        ),
      ),
    );
  }
}
