import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppColors {
  static const Color background = Color(0xFF0D1F0D);
  static const Color surface = Color(0xFF162916);
  static const Color surfaceLight = Color(0xFF1E3A1E);
  static const Color gold = Color(0xFFC8A96E);
  static const Color goldLight = Color(0xFFDFC799);
  static const Color cream = Color(0xFFF5F0E8);
  static const Color creamDim = Color(0xFFB8B0A4);
  static const Color ittifaq = Color(0xFF4CAF50);
  static const Color ikhtilaf = Color(0xFFE53935);
  static const Color tafsilat = Color(0xFFFF9800);
  static const Color confidenceAi = Color(0xFF9E9E9E);
  static const Color confidenceReviewed = Color(0xFF42A5F5);
  static const Color confidenceVerified = Color(0xFF66BB6A);
  static const Color divider = Color(0xFF2E4A2E);
}

class AppTheme {
  static TextStyle arabicBody({
    double fontSize = 18,
    Color color = AppColors.cream,
    FontWeight fontWeight = FontWeight.normal,
  }) {
    return GoogleFonts.amiri(
      fontSize: fontSize,
      color: color,
      fontWeight: fontWeight,
      height: 1.8,
    );
  }

  static TextStyle arabicTitle({
    double fontSize = 22,
    Color color = AppColors.gold,
    FontWeight fontWeight = FontWeight.bold,
  }) {
    return GoogleFonts.amiri(
      fontSize: fontSize,
      color: color,
      fontWeight: fontWeight,
      height: 1.6,
    );
  }

  static TextStyle arabicCaption({
    double fontSize = 14,
    Color color = AppColors.creamDim,
  }) {
    return GoogleFonts.amiri(
      fontSize: fontSize,
      color: color,
      height: 1.5,
    );
  }

  static ThemeData get darkTheme {
    return ThemeData(
      brightness: Brightness.dark,
      scaffoldBackgroundColor: AppColors.background,
      primaryColor: AppColors.gold,
      colorScheme: const ColorScheme.dark(
        primary: AppColors.gold,
        secondary: AppColors.goldLight,
        surface: AppColors.surface,
        onPrimary: AppColors.background,
        onSecondary: AppColors.background,
        onSurface: AppColors.cream,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: AppColors.surface,
        foregroundColor: AppColors.gold,
        elevation: 0,
        centerTitle: true,
        titleTextStyle: GoogleFonts.amiri(
          fontSize: 20,
          fontWeight: FontWeight.bold,
          color: AppColors.gold,
        ),
      ),
      bottomNavigationBarTheme: const BottomNavigationBarThemeData(
        backgroundColor: AppColors.surface,
        selectedItemColor: AppColors.gold,
        unselectedItemColor: AppColors.creamDim,
        type: BottomNavigationBarType.fixed,
      ),
      cardTheme: CardThemeData(
        color: AppColors.surface,
        elevation: 2,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
      ),
      dividerColor: AppColors.divider,
      chipTheme: ChipThemeData(
        backgroundColor: AppColors.surfaceLight,
        selectedColor: AppColors.gold,
        labelStyle: GoogleFonts.amiri(
          fontSize: 14,
          color: AppColors.cream,
        ),
        secondaryLabelStyle: GoogleFonts.amiri(
          fontSize: 14,
          color: AppColors.background,
        ),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
      ),
      expansionTileTheme: const ExpansionTileThemeData(
        iconColor: AppColors.gold,
        collapsedIconColor: AppColors.creamDim,
        textColor: AppColors.gold,
        collapsedTextColor: AppColors.cream,
      ),
      listTileTheme: ListTileThemeData(
        textColor: AppColors.cream,
        subtitleTextStyle: GoogleFonts.amiri(
          fontSize: 14,
          color: AppColors.creamDim,
        ),
      ),
      iconTheme: const IconThemeData(color: AppColors.gold),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: AppColors.surface,
        hintStyle: GoogleFonts.amiri(
          fontSize: 16,
          color: AppColors.creamDim,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: AppColors.gold, width: 2),
        ),
      ),
    );
  }
}
