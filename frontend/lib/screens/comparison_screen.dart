import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/taxonomy.dart';
import '../models/comparison.dart';
import '../providers/comparison_provider.dart';
import '../utils/constants.dart';
import '../utils/theme.dart';
import '../widgets/arabic_text.dart';

/// Standalone screen for a specific masala's comparison
class ComparisonScreen extends StatefulWidget {
  final Masala masala;

  const ComparisonScreen({super.key, required this.masala});

  @override
  State<ComparisonScreen> createState() => _ComparisonScreenState();
}

class _ComparisonScreenState extends State<ComparisonScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<ComparisonProvider>();
      provider.loadComparisons(widget.masala.id);
      provider.loadPositions(widget.masala.id);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.masala.titleAr,
          style: AppTheme.arabicTitle(fontSize: 18),
          overflow: TextOverflow.ellipsis,
        ),
      ),
      body: Consumer<ComparisonProvider>(
        builder: (context, provider, _) {
          if (provider.isLoadingComparisons || provider.isLoadingPositions) {
            return const Center(
              child: CircularProgressIndicator(color: AppColors.gold),
            );
          }

          if (provider.error != null) {
            return Center(
              child: ArabicText(provider.error!, color: AppColors.creamDim),
            );
          }

          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Summary cards
              ...provider.comparisons.map((c) => _buildSummaryCard(c)),
              if (provider.comparisons.isNotEmpty)
                const SizedBox(height: 16),
              // Positions header
              if (provider.positions.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: ArabicText(
                    'الأقوال والمواقف',
                    fontSize: 20,
                    color: AppColors.gold,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              // Position cards
              ...provider.positions.map((p) => _buildPositionCard(p)),
              if (provider.comparisons.isEmpty && provider.positions.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.only(top: 48),
                    child: ArabicText(
                      'لا توجد مقارنات متوفرة لهذه المسألة',
                      color: AppColors.creamDim,
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  Widget _buildSummaryCard(Comparison comparison) {
    Color resultColor;
    String resultLabel;
    switch (comparison.result) {
      case 'ittifaq':
        resultColor = AppColors.ittifaq;
        resultLabel = kComparisonLabels['ittifaq']!;
        break;
      case 'ikhtilaf':
        resultColor = AppColors.ikhtilaf;
        resultLabel = kComparisonLabels['ikhtilaf']!;
        break;
      default:
        resultColor = AppColors.tafsilat;
        resultLabel = kComparisonLabels['tafsilat']!;
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            // Result chip
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                _buildConfidenceBadge(comparison.confidence),
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                  decoration: BoxDecoration(
                    color: resultColor.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(color: resultColor, width: 1),
                  ),
                  child: Text(
                    resultLabel,
                    style: AppTheme.arabicBody(
                        fontSize: 14, color: resultColor),
                  ),
                ),
              ],
            ),
            if (comparison.summaryAr != null) ...[
              const SizedBox(height: 12),
              Text(
                comparison.summaryAr!,
                textDirection: TextDirection.rtl,
                textAlign: TextAlign.right,
                style: AppTheme.arabicBody(fontSize: 16, color: AppColors.cream),
              ),
            ],
            if (comparison.detailsAr != null) ...[
              const SizedBox(height: 8),
              _ExpandableDetails(details: comparison.detailsAr!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildPositionCard(Position position) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            // Book & author
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                _buildConfidenceBadge(position.confidence),
                const Spacer(),
                if (position.book != null)
                  Flexible(
                    child: Text(
                      position.book!.titleAr,
                      style: AppTheme.arabicBody(
                          fontSize: 15, color: AppColors.goldLight),
                      textDirection: TextDirection.rtl,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
              ],
            ),
            if (position.book?.author != null) ...[
              const SizedBox(height: 4),
              Text(
                position.book!.author!.nameAr,
                style: AppTheme.arabicCaption(fontSize: 13),
                textDirection: TextDirection.rtl,
              ),
            ],
            const Divider(height: 20),
            // Hukm chip
            if (position.hukm != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppColors.gold.withValues(alpha: 0.15),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    position.hukm!,
                    style: AppTheme.arabicBody(
                        fontSize: 14, color: AppColors.gold),
                  ),
                ),
              ),
            // Hukm text
            if (position.hukmTextAr != null)
              Text(
                position.hukmTextAr!,
                textDirection: TextDirection.rtl,
                textAlign: TextAlign.right,
                style: AppTheme.arabicBody(fontSize: 16, color: AppColors.cream),
              ),
            // Dalil
            if (position.dalilAr != null) ...[
              const SizedBox(height: 8),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.surfaceLight,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.divider),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      'الدليل:',
                      style: AppTheme.arabicCaption(
                          fontSize: 13, color: AppColors.gold),
                      textDirection: TextDirection.rtl,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      position.dalilAr!,
                      textDirection: TextDirection.rtl,
                      textAlign: TextAlign.right,
                      style: AppTheme.arabicBody(
                          fontSize: 15, color: AppColors.creamDim),
                    ),
                  ],
                ),
              ),
            ],
            // Conditions
            if (position.conditionsAr != null) ...[
              const SizedBox(height: 8),
              Text(
                'الشروط: ${position.conditionsAr}',
                textDirection: TextDirection.rtl,
                textAlign: TextAlign.right,
                style: AppTheme.arabicCaption(fontSize: 14),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildConfidenceBadge(String confidence) {
    Color color;
    String label;
    switch (confidence) {
      case 'verified':
        color = AppColors.confidenceVerified;
        label = kConfidenceLabels['verified']!;
        break;
      case 'reviewed':
        color = AppColors.confidenceReviewed;
        label = kConfidenceLabels['reviewed']!;
        break;
      default:
        color = AppColors.confidenceAi;
        label = kConfidenceLabels['ai']!;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.2),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Text(
        label,
        style: AppTheme.arabicCaption(fontSize: 11, color: color),
      ),
    );
  }
}

/// Expandable details section
class _ExpandableDetails extends StatefulWidget {
  final String details;

  const _ExpandableDetails({required this.details});

  @override
  State<_ExpandableDetails> createState() => _ExpandableDetailsState();
}

class _ExpandableDetailsState extends State<_ExpandableDetails> {
  bool _expanded = false;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              Icon(
                _expanded ? Icons.expand_less : Icons.expand_more,
                color: AppColors.gold,
                size: 20,
              ),
              const SizedBox(width: 4),
              Text(
                _expanded ? 'إخفاء التفاصيل' : 'عرض التفاصيل',
                style: AppTheme.arabicCaption(
                    fontSize: 13, color: AppColors.gold),
              ),
            ],
          ),
        ),
        if (_expanded) ...[
          const SizedBox(height: 8),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.surfaceLight,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              widget.details,
              textDirection: TextDirection.rtl,
              textAlign: TextAlign.right,
              style: AppTheme.arabicBody(
                  fontSize: 15, color: AppColors.creamDim),
            ),
          ),
        ],
      ],
    );
  }
}

/// Tab screen that shows a list of recent/featured comparisons
class ComparisonListScreen extends StatelessWidget {
  const ComparisonListScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.compare_arrows,
              size: 80,
              color: AppColors.gold.withValues(alpha: 0.4),
            ),
            const SizedBox(height: 24),
            const ArabicText(
              'المقارنة بين الأقوال',
              fontSize: 22,
              color: AppColors.gold,
              fontWeight: FontWeight.bold,
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 12),
            const ArabicText(
              'اختر مسألة من تبويب "الأبواب" لعرض المقارنة بين أقوال العلماء فيها',
              fontSize: 16,
              color: AppColors.creamDim,
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }
}
