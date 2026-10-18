#include <QCoreApplication>
#include <QFile>
#include <QJSEngine>
#include <QJSValue>
#include <QTextStream>

int main(int argc, char **argv) {
  QCoreApplication app(argc, argv);
  if (argc != 2) return 2;
  QFile source(QString::fromLocal8Bit(argv[1]));
  if (!source.open(QIODevice::ReadOnly)) return 2;
  QJSEngine engine;
  engine.installExtensions(QJSEngine::GarbageCollectionExtension);
  const auto result = engine.evaluate(QString::fromUtf8(source.readAll()), source.fileName());
  if (result.isError()) {
    QTextStream(stderr) << "QT_SETLOOKUP_PROBE_FAIL line="
                        << result.property("lineNumber").toInt() << " "
                        << result.toString() << Qt::endl;
    return 1;
  }
  if (result.toString() != QStringLiteral("QT_SETLOOKUP_PROBE_PASS")) return 1;
  QTextStream(stdout) << result.toString() << Qt::endl;
  return 0;
}
