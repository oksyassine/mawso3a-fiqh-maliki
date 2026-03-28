const String kAppName = 'موسوعة الفقه المالكي';
const String kAppNameEn = 'Mawso3a Fiqh Maliki';
const String kApiBaseUrl = 'https://mawso3a.learn.nucleuselmers.org/api/v1';

// Study levels
const String kLevelBeginner = 'beginner';
const String kLevelIntermediate = 'intermediate';
const String kLevelAdvanced = 'advanced';
const String kLevelSpecialist = 'specialist';

const Map<String, String> kStudyLevelLabels = {
  kLevelBeginner: 'مبتدئ',
  kLevelIntermediate: 'متوسط',
  kLevelAdvanced: 'متقدم',
  kLevelSpecialist: 'متخصص',
};

// Text types
const Map<String, String> kTextTypeLabels = {
  'matn': 'متن',
  'sharh': 'شرح',
  'hashiya': 'حاشية',
  'nazm': 'نظم',
  'fatawa': 'فتاوى',
  'encyclopedia': 'موسوعة',
};

// Comparison results
const Map<String, String> kComparisonLabels = {
  'ittifaq': 'اتفاق',
  'ikhtilaf': 'اختلاف',
  'tafsilat': 'تفصيلات',
};

// Confidence levels
const Map<String, String> kConfidenceLabels = {
  'ai': 'ذكاء اصطناعي',
  'reviewed': 'مراجع',
  'verified': 'موثق',
};
