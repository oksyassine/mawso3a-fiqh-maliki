import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'utils/constants.dart';
import 'utils/theme.dart';
import 'providers/library_provider.dart';
import 'providers/taxonomy_provider.dart';
import 'providers/comparison_provider.dart';
import 'screens/home_screen.dart';
import 'screens/search_screen.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MawsoaFiqhApp());
}

class MawsoaFiqhApp extends StatelessWidget {
  const MawsoaFiqhApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => LibraryProvider()),
        ChangeNotifierProvider(create: (_) => TaxonomyProvider()),
        ChangeNotifierProvider(create: (_) => ComparisonProvider()),
      ],
      child: Builder(
        builder: (context) {
          return Directionality(
            textDirection: TextDirection.rtl,
            child: MaterialApp(
              title: kAppName,
              debugShowCheckedModeBanner: false,
              theme: AppTheme.darkTheme,
              locale: const Locale('ar'),
              home: const HomeScreen(),
              routes: {
                '/home': (_) => const HomeScreen(),
                '/search': (_) => const Scaffold(body: SearchScreen()),
              },
            ),
          );
        },
      ),
    );
  }
}
