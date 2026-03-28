class Author {
  final int id;
  final String nameAr;
  final String? nameEn;
  final int? deathHijri;
  final int? deathCe;
  final String? region;

  Author({
    required this.id,
    required this.nameAr,
    this.nameEn,
    this.deathHijri,
    this.deathCe,
    this.region,
  });

  factory Author.fromJson(Map<String, dynamic> json) {
    return Author(
      id: json['id'] as int,
      nameAr: json['name_ar'] as String,
      nameEn: json['name_en'] as String?,
      deathHijri: json['death_hijri'] as int?,
      deathCe: json['death_ce'] as int?,
      region: json['region'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name_ar': nameAr,
      'name_en': nameEn,
      'death_hijri': deathHijri,
      'death_ce': deathCe,
      'region': region,
    };
  }
}

class Book {
  final int id;
  final String titleAr;
  final String? titleEn;
  final String? shortTitleAr;
  final Author? author;
  final String textType;
  final String? studyLevel;
  final int? parentBookId;
  final String? descriptionAr;
  final List<Book>? commentaries;

  Book({
    required this.id,
    required this.titleAr,
    this.titleEn,
    this.shortTitleAr,
    this.author,
    required this.textType,
    this.studyLevel,
    this.parentBookId,
    this.descriptionAr,
    this.commentaries,
  });

  factory Book.fromJson(Map<String, dynamic> json) {
    return Book(
      id: json['id'] as int,
      titleAr: json['title_ar'] as String,
      titleEn: json['title_en'] as String?,
      shortTitleAr: json['short_title_ar'] as String?,
      author: json['author'] != null
          ? Author.fromJson(json['author'] as Map<String, dynamic>)
          : null,
      textType: json['text_type'] as String? ?? 'matn',
      studyLevel: json['study_level'] as String?,
      parentBookId: json['parent_book_id'] as int?,
      descriptionAr: json['description_ar'] as String?,
      commentaries: json['commentaries'] != null
          ? (json['commentaries'] as List<dynamic>)
              .map((e) => Book.fromJson(e as Map<String, dynamic>))
              .toList()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title_ar': titleAr,
      'title_en': titleEn,
      'short_title_ar': shortTitleAr,
      'author': author?.toJson(),
      'text_type': textType,
      'study_level': studyLevel,
      'parent_book_id': parentBookId,
      'description_ar': descriptionAr,
      'commentaries': commentaries?.map((e) => e.toJson()).toList(),
    };
  }
}

class Chapter {
  final int id;
  final int bookId;
  final String titleAr;
  final int order;
  final int? parentChapterId;

  Chapter({
    required this.id,
    required this.bookId,
    required this.titleAr,
    required this.order,
    this.parentChapterId,
  });

  factory Chapter.fromJson(Map<String, dynamic> json) {
    return Chapter(
      id: json['id'] as int,
      bookId: json['book_id'] as int,
      titleAr: json['title_ar'] as String,
      order: json['order'] as int,
      parentChapterId: json['parent_chapter_id'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'book_id': bookId,
      'title_ar': titleAr,
      'order': order,
      'parent_chapter_id': parentChapterId,
    };
  }
}

class Passage {
  final int id;
  final int chapterId;
  final String textAr;
  final int order;
  final int? pageNumber;

  Passage({
    required this.id,
    required this.chapterId,
    required this.textAr,
    required this.order,
    this.pageNumber,
  });

  factory Passage.fromJson(Map<String, dynamic> json) {
    return Passage(
      id: json['id'] as int,
      chapterId: json['chapter_id'] as int,
      textAr: json['text_ar'] as String,
      order: json['order'] as int,
      pageNumber: json['page_number'] as int?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'chapter_id': chapterId,
      'text_ar': textAr,
      'order': order,
      'page_number': pageNumber,
    };
  }
}
