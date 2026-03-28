import 'book.dart';

class Position {
  final int id;
  final int masalaId;
  final String? hukm;
  final String? hukmTextAr;
  final String? dalilAr;
  final String? conditionsAr;
  final String confidence;
  final Book? book;
  final Passage? passage;

  Position({
    required this.id,
    required this.masalaId,
    this.hukm,
    this.hukmTextAr,
    this.dalilAr,
    this.conditionsAr,
    required this.confidence,
    this.book,
    this.passage,
  });

  factory Position.fromJson(Map<String, dynamic> json) {
    return Position(
      id: json['id'] as int,
      masalaId: json['masala_id'] as int,
      hukm: json['hukm'] as String?,
      hukmTextAr: json['hukm_text_ar'] as String?,
      dalilAr: json['dalil_ar'] as String?,
      conditionsAr: json['conditions_ar'] as String?,
      confidence: json['confidence'] as String? ?? 'ai',
      book: json['book'] != null
          ? Book.fromJson(json['book'] as Map<String, dynamic>)
          : null,
      passage: json['passage'] != null
          ? Passage.fromJson(json['passage'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'masala_id': masalaId,
      'hukm': hukm,
      'hukm_text_ar': hukmTextAr,
      'dalil_ar': dalilAr,
      'conditions_ar': conditionsAr,
      'confidence': confidence,
      'book': book?.toJson(),
      'passage': passage?.toJson(),
    };
  }
}

class Comparison {
  final int id;
  final int masalaId;
  final String result;
  final String? summaryAr;
  final String? detailsAr;
  final String confidence;
  final List<Position>? positions;

  Comparison({
    required this.id,
    required this.masalaId,
    required this.result,
    this.summaryAr,
    this.detailsAr,
    required this.confidence,
    this.positions,
  });

  factory Comparison.fromJson(Map<String, dynamic> json) {
    return Comparison(
      id: json['id'] as int,
      masalaId: json['masala_id'] as int,
      result: json['result'] as String? ?? 'tafsilat',
      summaryAr: json['summary_ar'] as String?,
      detailsAr: json['details_ar'] as String?,
      confidence: json['confidence'] as String? ?? 'ai',
      positions: json['positions'] != null
          ? (json['positions'] as List<dynamic>)
              .map((e) => Position.fromJson(e as Map<String, dynamic>))
              .toList()
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'masala_id': masalaId,
      'result': result,
      'summary_ar': summaryAr,
      'details_ar': detailsAr,
      'confidence': confidence,
      'positions': positions?.map((e) => e.toJson()).toList(),
    };
  }
}
