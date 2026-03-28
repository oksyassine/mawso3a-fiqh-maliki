import 'package:sqflite/sqflite.dart';
import '../models/book.dart';
import 'api_service.dart';

class LocalDb {
  static final LocalDb _instance = LocalDb._internal();
  factory LocalDb() => _instance;
  LocalDb._internal();

  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDb();
    return _db!;
  }

  Future<Database> _initDb() async {
    final dbPath = await getDatabasesPath();
    final path = '$dbPath/mawso3a_fiqh.db';
    return openDatabase(
      path,
      version: 1,
      onCreate: _onCreate,
    );
  }

  Future<void> _onCreate(Database db, int version) async {
    await db.execute('''
      CREATE TABLE books (
        id INTEGER PRIMARY KEY,
        title_ar TEXT NOT NULL,
        title_en TEXT,
        short_title_ar TEXT,
        author_json TEXT,
        text_type TEXT NOT NULL,
        study_level TEXT,
        parent_book_id INTEGER,
        description_ar TEXT,
        downloaded INTEGER NOT NULL DEFAULT 0
      )
    ''');

    await db.execute('''
      CREATE TABLE chapters (
        id INTEGER PRIMARY KEY,
        book_id INTEGER NOT NULL,
        title_ar TEXT NOT NULL,
        sort_order INTEGER NOT NULL,
        parent_chapter_id INTEGER,
        FOREIGN KEY (book_id) REFERENCES books(id)
      )
    ''');

    await db.execute('''
      CREATE TABLE passages (
        id INTEGER PRIMARY KEY,
        chapter_id INTEGER NOT NULL,
        text_ar TEXT NOT NULL,
        sort_order INTEGER NOT NULL,
        page_number INTEGER,
        FOREIGN KEY (chapter_id) REFERENCES chapters(id)
      )
    ''');

    await db.execute('''
      CREATE TABLE bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id INTEGER NOT NULL,
        chapter_id INTEGER NOT NULL,
        passage_id INTEGER,
        note TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (book_id) REFERENCES books(id),
        FOREIGN KEY (chapter_id) REFERENCES chapters(id)
      )
    ''');

    await db.execute(
        'CREATE INDEX idx_chapters_book ON chapters(book_id)');
    await db.execute(
        'CREATE INDEX idx_passages_chapter ON passages(chapter_id)');
    await db.execute(
        'CREATE INDEX idx_bookmarks_book ON bookmarks(book_id)');
  }

  // Cache a book record
  Future<void> cacheBook(Book book) async {
    final db = await database;
    await db.insert(
      'books',
      {
        'id': book.id,
        'title_ar': book.titleAr,
        'title_en': book.titleEn,
        'short_title_ar': book.shortTitleAr,
        'author_json': book.author != null
            ? '${book.author!.nameAr}|${book.author!.deathHijri ?? ""}'
            : null,
        'text_type': book.textType,
        'study_level': book.studyLevel,
        'parent_book_id': book.parentBookId,
        'description_ar': book.descriptionAr,
        'downloaded': 0,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  // Get a cached book
  Future<Book?> getCachedBook(int bookId) async {
    final db = await database;
    final rows = await db.query('books', where: 'id = ?', whereArgs: [bookId]);
    if (rows.isEmpty) return null;
    final row = rows.first;
    Author? author;
    if (row['author_json'] != null) {
      final parts = (row['author_json'] as String).split('|');
      author = Author(
        id: 0,
        nameAr: parts[0],
        deathHijri: parts.length > 1 && parts[1].isNotEmpty
            ? int.tryParse(parts[1])
            : null,
      );
    }
    return Book(
      id: row['id'] as int,
      titleAr: row['title_ar'] as String,
      titleEn: row['title_en'] as String?,
      shortTitleAr: row['short_title_ar'] as String?,
      author: author,
      textType: row['text_type'] as String,
      studyLevel: row['study_level'] as String?,
      parentBookId: row['parent_book_id'] as int?,
      descriptionAr: row['description_ar'] as String?,
    );
  }

  // Get cached passages for a chapter
  Future<List<Passage>> getCachedPassages(int chapterId) async {
    final db = await database;
    final rows = await db.query(
      'passages',
      where: 'chapter_id = ?',
      whereArgs: [chapterId],
      orderBy: 'sort_order',
    );
    return rows
        .map((row) => Passage(
              id: row['id'] as int,
              chapterId: row['chapter_id'] as int,
              textAr: row['text_ar'] as String,
              order: row['sort_order'] as int,
              pageNumber: row['page_number'] as int?,
            ))
        .toList();
  }

  // Get cached chapters for a book
  Future<List<Chapter>> getCachedChapters(int bookId) async {
    final db = await database;
    final rows = await db.query(
      'chapters',
      where: 'book_id = ?',
      whereArgs: [bookId],
      orderBy: 'sort_order',
    );
    return rows
        .map((row) => Chapter(
              id: row['id'] as int,
              bookId: row['book_id'] as int,
              titleAr: row['title_ar'] as String,
              order: row['sort_order'] as int,
              parentChapterId: row['parent_chapter_id'] as int?,
            ))
        .toList();
  }

  // Check if a book is fully downloaded
  Future<bool> isBookDownloaded(int bookId) async {
    final db = await database;
    final rows = await db.query(
      'books',
      columns: ['downloaded'],
      where: 'id = ?',
      whereArgs: [bookId],
    );
    if (rows.isEmpty) return false;
    return rows.first['downloaded'] == 1;
  }

  // Download a full book (chapters + passages) from API and cache locally
  Future<void> downloadBook(int bookId) async {
    final api = ApiService();
    final db = await database;

    final chapters = await api.getChapters(bookId);
    final batch = db.batch();

    for (final ch in chapters) {
      batch.insert(
        'chapters',
        {
          'id': ch.id,
          'book_id': ch.bookId,
          'title_ar': ch.titleAr,
          'sort_order': ch.order,
          'parent_chapter_id': ch.parentChapterId,
        },
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);

    for (final ch in chapters) {
      final passages = await api.getPassages(bookId, ch.id);
      final pBatch = db.batch();
      for (final ps in passages) {
        pBatch.insert(
          'passages',
          {
            'id': ps.id,
            'chapter_id': ps.chapterId,
            'text_ar': ps.textAr,
            'sort_order': ps.order,
            'page_number': ps.pageNumber,
          },
          conflictAlgorithm: ConflictAlgorithm.replace,
        );
      }
      await pBatch.commit(noResult: true);
    }

    await db.update(
      'books',
      {'downloaded': 1},
      where: 'id = ?',
      whereArgs: [bookId],
    );
  }

  // Bookmarks
  Future<int> addBookmark({
    required int bookId,
    required int chapterId,
    int? passageId,
    String? note,
  }) async {
    final db = await database;
    return db.insert('bookmarks', {
      'book_id': bookId,
      'chapter_id': chapterId,
      'passage_id': passageId,
      'note': note,
      'created_at': DateTime.now().toIso8601String(),
    });
  }

  Future<void> removeBookmark(int id) async {
    final db = await database;
    await db.delete('bookmarks', where: 'id = ?', whereArgs: [id]);
  }

  Future<List<Map<String, dynamic>>> getBookmarks({int? bookId}) async {
    final db = await database;
    if (bookId != null) {
      return db.query('bookmarks',
          where: 'book_id = ?',
          whereArgs: [bookId],
          orderBy: 'created_at DESC');
    }
    return db.query('bookmarks', orderBy: 'created_at DESC');
  }

  Future<bool> isBookmarked(int chapterId, {int? passageId}) async {
    final db = await database;
    final where = passageId != null
        ? 'chapter_id = ? AND passage_id = ?'
        : 'chapter_id = ?';
    final whereArgs =
        passageId != null ? [chapterId, passageId] : [chapterId];
    final rows =
        await db.query('bookmarks', where: where, whereArgs: whereArgs);
    return rows.isNotEmpty;
  }

  Future<void> close() async {
    final db = await database;
    await db.close();
    _db = null;
  }
}
