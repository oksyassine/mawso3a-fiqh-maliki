class FiqhCategory {
  final int id;
  final String nameAr;
  final String? nameEn;
  final int? parentId;
  final List<FiqhCategory>? subcategories;

  FiqhCategory({
    required this.id,
    required this.nameAr,
    this.nameEn,
    this.parentId,
    this.subcategories,
  });

  factory FiqhCategory.fromJson(Map<String, dynamic> json) {
    return FiqhCategory(
      id: json['id'] as int,
      nameAr: json['name_ar'] as String,
      nameEn: json['name_en'] as String?,
      parentId: json['parent_id'] as int?,
      subcategories: json['subcategories'] != null
          ? (json['subcategories'] as List<dynamic>)
              .map((e) => FiqhCategory.fromJson(e as Map<String, dynamic>))
              .toList()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name_ar': nameAr,
      'name_en': nameEn,
      'parent_id': parentId,
      'subcategories': subcategories?.map((e) => e.toJson()).toList(),
    };
  }
}

class Masala {
  final int id;
  final int categoryId;
  final String titleAr;
  final String? descriptionAr;

  Masala({
    required this.id,
    required this.categoryId,
    required this.titleAr,
    this.descriptionAr,
  });

  factory Masala.fromJson(Map<String, dynamic> json) {
    return Masala(
      id: json['id'] as int,
      categoryId: json['category_id'] as int,
      titleAr: json['title_ar'] as String,
      descriptionAr: json['description_ar'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'category_id': categoryId,
      'title_ar': titleAr,
      'description_ar': descriptionAr,
    };
  }
}
