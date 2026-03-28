import 'package:flutter_test/flutter_test.dart';
import 'package:mawso3a_fiqh/main.dart';

void main() {
  testWidgets('App loads smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const MawsoaFiqhApp());
    await tester.pump();
  });
}
