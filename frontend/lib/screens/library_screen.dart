import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/library_provider.dart';
import '../models/book.dart';
import '../utils/constants.dart';
import '../utils/theme.dart';
import '../widgets/arabic_text.dart';
import 'book_reader_screen.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  String? _selectedLevel;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<LibraryProvider>();
      if (provider.mutoon.isEmpty) {
        provider.loadMutoon();
      }
    });
  }

  List<Book> _filteredBooks(List<Book> books) {
    if (_selectedLevel == null) return books;
    return books.where((b) => b.studyLevel == _selectedLevel).toList();
  }

  Map<String, List<Book>> _groupByLevel(List<Book> books) {
    final grouped = <String, List<Book>>{};
    for (final level in [
      kLevelBeginner,
      kLevelIntermediate,
      kLevelAdvanced,
      kLevelSpecialist,
    ]) {
      final levelBooks = books.where((b) => b.studyLevel == level).toList();
      if (levelBooks.isNotEmpty) {
        grouped[level] = levelBooks;
      }
    }
    // Books without a level
    final noLevel = books.where((b) => b.studyLevel == null).toList();
    if (noLevel.isNotEmpty) {
      grouped['other'] = noLevel;
    }
    return grouped;
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<LibraryProvider>(
      builder: (context, provider, _) {
        if (provider.isLoadingBooks) {
          return const Center(
            child: CircularProgressIndicator(color: AppColors.gold),
          );
        }

        if (provider.error != null && provider.mutoon.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.cloud_off, size: 64, color: AppColors.creamDim),
                const SizedBox(height: 16),
                ArabicText(provider.error!, color: AppColors.creamDim),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: provider.loadMutoon,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.gold,
                    foregroundColor: AppColors.background,
                  ),
                  child: const ArabicText('إعادة المحاولة', fontSize: 16),
                ),
              ],
            ),
          );
        }

        final filtered = _filteredBooks(provider.mutoon);
        final grouped = _groupByLevel(filtered);

        return Column(
          children: [
            // Filter chips
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              reverse: true,
              child: Row(
                children: [
                  _buildFilterChip(null, 'الكل'),
                  const SizedBox(width: 8),
                  ...kStudyLevelLabels.entries.map(
                    (e) => Padding(
                      padding: const EdgeInsets.only(left: 8),
                      child: _buildFilterChip(e.key, e.value),
                    ),
                  ),
                ],
              ),
            ),
            const Divider(height: 1),
            // Book list
            Expanded(
              child: grouped.isEmpty
                  ? const Center(
                      child: ArabicText('لا توجد كتب', color: AppColors.creamDim),
                    )
                  : ListView(
                      padding: const EdgeInsets.only(bottom: 16),
                      children: grouped.entries.map((entry) {
                        final levelLabel = entry.key == 'other'
                            ? 'أخرى'
                            : kStudyLevelLabels[entry.key] ?? entry.key;
                        return _buildLevelSection(
                            levelLabel, entry.value, context);
                      }).toList(),
                    ),
            ),
          ],
        );
      },
    );
  }

  Widget _buildFilterChip(String? level, String label) {
    final selected = _selectedLevel == level;
    return FilterChip(
      label: Text(label),
      selected: selected,
      onSelected: (val) {
        setState(() => _selectedLevel = val ? level : null);
      },
      selectedColor: AppColors.gold,
      checkmarkColor: AppColors.background,
      labelStyle: AppTheme.arabicCaption(
        color: selected ? AppColors.background : AppColors.cream,
      ),
    );
  }

  Widget _buildLevelSection(
      String levelLabel, List<Book> books, BuildContext context) {
    return ExpansionTile(
      initiallyExpanded: true,
      title: Text(
        levelLabel,
        style: AppTheme.arabicTitle(fontSize: 18),
        textDirection: TextDirection.rtl,
      ),
      trailing: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: AppColors.gold.withValues(alpha: 0.2),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Text(
          '${books.length}',
          style: AppTheme.arabicCaption(color: AppColors.gold),
        ),
      ),
      children: books.map((book) => _buildBookTile(book, context)).toList(),
    );
  }

  Widget _buildBookTile(Book book, BuildContext context) {
    final authorInfo = book.author != null
        ? '${book.author!.nameAr}${book.author!.deathHijri != null ? " (ت ${book.author!.deathHijri} هـ)" : ""}'
        : '';
    final commentaryCount = book.commentaries?.length ?? 0;

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
      title: Text(
        book.titleAr,
        style: AppTheme.arabicBody(fontSize: 17, color: AppColors.cream),
        textDirection: TextDirection.rtl,
      ),
      subtitle: authorInfo.isNotEmpty
          ? Text(
              authorInfo,
              style: AppTheme.arabicCaption(fontSize: 13),
              textDirection: TextDirection.rtl,
            )
          : null,
      leading: commentaryCount > 0
          ? Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.surfaceLight,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                '$commentaryCount شرح',
                style: AppTheme.arabicCaption(fontSize: 11, color: AppColors.goldLight),
              ),
            )
          : null,
      trailing: Icon(
        _iconForTextType(book.textType),
        color: AppColors.creamDim,
        size: 20,
      ),
      onTap: () {
        context.read<LibraryProvider>().selectBook(book);
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (_) => BookReaderScreen(book: book),
          ),
        );
      },
    );
  }

  IconData _iconForTextType(String textType) {
    switch (textType) {
      case 'matn':
        return Icons.menu_book;
      case 'sharh':
        return Icons.comment;
      case 'hashiya':
        return Icons.note;
      case 'nazm':
        return Icons.music_note;
      case 'fatawa':
        return Icons.question_answer;
      case 'encyclopedia':
        return Icons.collections_bookmark;
      default:
        return Icons.book;
    }
  }
}
