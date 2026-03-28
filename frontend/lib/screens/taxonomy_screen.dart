import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/taxonomy_provider.dart';
import '../models/taxonomy.dart';
import '../utils/theme.dart';
import '../widgets/arabic_text.dart';
import 'comparison_screen.dart';

class TaxonomyScreen extends StatefulWidget {
  const TaxonomyScreen({super.key});

  @override
  State<TaxonomyScreen> createState() => _TaxonomyScreenState();
}

class _TaxonomyScreenState extends State<TaxonomyScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final provider = context.read<TaxonomyProvider>();
      if (provider.categories.isEmpty) {
        provider.loadCategories();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<TaxonomyProvider>(
      builder: (context, provider, _) {
        if (provider.isLoadingCategories) {
          return const Center(
            child: CircularProgressIndicator(color: AppColors.gold),
          );
        }

        if (provider.error != null && provider.categories.isEmpty) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                const Icon(Icons.cloud_off,
                    size: 64, color: AppColors.creamDim),
                const SizedBox(height: 16),
                ArabicText(provider.error!, color: AppColors.creamDim),
                const SizedBox(height: 16),
                ElevatedButton(
                  onPressed: provider.loadCategories,
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

        if (provider.categories.isEmpty) {
          return const Center(
            child: ArabicText('لا توجد أبواب فقهية', color: AppColors.creamDim),
          );
        }

        return ListView.builder(
          padding: const EdgeInsets.only(bottom: 16),
          itemCount: provider.categories.length,
          itemBuilder: (context, index) {
            return _buildCategoryTile(provider.categories[index], provider);
          },
        );
      },
    );
  }

  Widget _buildCategoryTile(FiqhCategory category, TaxonomyProvider provider) {
    final subs = category.subcategories ?? [];

    if (subs.isEmpty) {
      return ListTile(
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 20, vertical: 2),
        title: Text(
          category.nameAr,
          style: AppTheme.arabicBody(fontSize: 17, color: AppColors.cream),
          textDirection: TextDirection.rtl,
        ),
        trailing: const Icon(Icons.arrow_back_ios, size: 16),
        onTap: () {
          provider.selectCategory(category);
          _showMasailSheet(context, category, provider);
        },
      );
    }

    return ExpansionTile(
      tilePadding: const EdgeInsets.symmetric(horizontal: 20),
      title: Text(
        category.nameAr,
        style: AppTheme.arabicTitle(fontSize: 18),
        textDirection: TextDirection.rtl,
      ),
      children: subs.map((sub) {
        final masailCount = sub.subcategories?.length ?? 0;
        return ListTile(
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 36, vertical: 0),
          title: Text(
            sub.nameAr,
            style: AppTheme.arabicBody(fontSize: 16, color: AppColors.cream),
            textDirection: TextDirection.rtl,
          ),
          trailing: masailCount > 0
              ? Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: AppColors.gold.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Text(
                    '$masailCount',
                    style: AppTheme.arabicCaption(
                        fontSize: 12, color: AppColors.gold),
                  ),
                )
              : null,
          onTap: () {
            provider.selectCategory(sub);
            _showMasailSheet(context, sub, provider);
          },
        );
      }).toList(),
    );
  }

  void _showMasailSheet(
      BuildContext context, FiqhCategory category, TaxonomyProvider provider) {
    showModalBottomSheet(
      context: context,
      backgroundColor: AppColors.surface,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) {
        return DraggableScrollableSheet(
          initialChildSize: 0.6,
          minChildSize: 0.3,
          maxChildSize: 0.9,
          expand: false,
          builder: (context, scrollController) {
            return Consumer<TaxonomyProvider>(
              builder: (context, prov, _) {
                return Column(
                  children: [
                    Container(
                      width: 40,
                      height: 4,
                      margin: const EdgeInsets.symmetric(vertical: 12),
                      decoration: BoxDecoration(
                        color: AppColors.creamDim,
                        borderRadius: BorderRadius.circular(2),
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      child: ArabicText(
                        category.nameAr,
                        fontSize: 20,
                        color: AppColors.gold,
                        fontWeight: FontWeight.bold,
                        textAlign: TextAlign.center,
                      ),
                    ),
                    const Divider(height: 24),
                    if (prov.isLoadingMasail)
                      const Expanded(
                        child: Center(
                          child: CircularProgressIndicator(
                              color: AppColors.gold),
                        ),
                      )
                    else if (prov.masail.isEmpty)
                      const Expanded(
                        child: Center(
                          child: ArabicText('لا توجد مسائل',
                              color: AppColors.creamDim),
                        ),
                      )
                    else
                      Expanded(
                        child: ListView.separated(
                          controller: scrollController,
                          padding: const EdgeInsets.symmetric(horizontal: 16),
                          itemCount: prov.masail.length,
                          separatorBuilder: (_, index2) =>
                              const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final masala = prov.masail[index];
                            return ListTile(
                              title: Text(
                                masala.titleAr,
                                style: AppTheme.arabicBody(
                                    fontSize: 16, color: AppColors.cream),
                                textDirection: TextDirection.rtl,
                              ),
                              subtitle: masala.descriptionAr != null
                                  ? Text(
                                      masala.descriptionAr!,
                                      style: AppTheme.arabicCaption(
                                          fontSize: 13),
                                      textDirection: TextDirection.rtl,
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                    )
                                  : null,
                              trailing: const Icon(Icons.arrow_back_ios,
                                  size: 14, color: AppColors.creamDim),
                              onTap: () {
                                Navigator.pop(context);
                                Navigator.push(
                                  context,
                                  MaterialPageRoute(
                                    builder: (_) =>
                                        ComparisonScreen(masala: masala),
                                  ),
                                );
                              },
                            );
                          },
                        ),
                      ),
                  ],
                );
              },
            );
          },
        );
      },
    );
  }
}
