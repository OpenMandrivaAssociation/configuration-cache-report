Name:		configuration-cache-report
Version:	1.36
Release:	1
Summary:	Gradle configuration cache HTML report model
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/gradle/configuration-cache-report
# configuration-cache-report commit 149a37caad31 (version 1.36, not a tag).
# JVM classes for org.gradle.buildtool.internal:configuration-cache-report.
# The HTML shell is the upstream page. Webpack does not inline the JS bundle.
Source0:	configuration-cache-report-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-time-instant)
BuildRequires:	mvn(org.jetbrains.kotlinx:kotlinx-serialization-core)
BuildRequires:	mvn(org.jetbrains.kotlinx:kotlinx-serialization-json)
BuildRequires:	mvn(org.jetbrains:annotations)

%description
org.gradle.buildtool.internal:configuration-cache-report %{version}.
JVM report model and HtmlReportWriter from commit 149a37caad31,
compiled with kotlinc 2.0.21 and the serialization compiler plugin.
The bundled HTML shell is the upstream page source. The JS application
is not inlined. HtmlReportWriter still emits the JSON script elements.

%prep
%autosetup -n configuration-cache-report-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
test -s src/resources/configuration-cache-report.html
grep -F -q 'src="configuration-cache-report-data.js"' src/resources/configuration-cache-report.html

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
CORE=%{_javadir}/kotlinx-serialization-core.jar
JSON=%{_javadir}/kotlinx-serialization-json.jar
ANN=%{_javadir}/org.jetbrains.annotations.jar
PLUGIN=/usr/share/kotlin/lib/kotlinx-serialization-compiler-plugin.jar
test -s "$STDLIB"
test -s "$INSTANT"
test -s "$CORE"
test -s "$JSON"
test -s "$ANN"
test -s "$PLUGIN"
mkdir -p classes
find src/common src/jvm -name '*.kt' | sort > sources.list
test "$(wc -l < sources.list)" -eq 9
kotlinc -J-Xmx2g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-Xplugin="$PLUGIN" \
	-opt-in=kotlinx.serialization.ExperimentalSerializationApi \
	-cp "$STDLIB:$INSTANT:$CORE:$JSON:$ANN" -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 94
test -s classes/org/gradle/problems/internal/report/HtmlReportWriter.class
mkdir -p classes/org/gradle/problems/internal/report
cp -f src/resources/configuration-cache-report.html classes/org/gradle/problems/internal/report/
test -s classes/org/gradle/problems/internal/report/configuration-cache-report.html
printf '%s\n' 'Manifest-Version: 1.0' 'Automatic-Module-Name: configuration.cache.report' > manifest.mf
jar cfm configuration-cache-report.jar manifest.mf -C classes .
jar i configuration-cache-report.jar
desc=$(jar --describe-module --file configuration-cache-report.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'configuration.cache.report automatic'
cat > configuration-cache-report.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.gradle.buildtool.internal</groupId>
  <artifactId>configuration-cache-report</artifactId>
  <version>%{version}</version>
  <name>configuration-cache-report</name>
  <description>Gradle configuration cache HTML report model</description>
  <url>https://github.com/gradle/configuration-cache-report</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>2.0.21</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlinx</groupId>
      <artifactId>kotlinx-serialization-core</artifactId>
      <version>1.11.0</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlinx</groupId>
      <artifactId>kotlinx-serialization-json</artifactId>
      <version>1.11.0</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact configuration-cache-report.pom:configuration-cache-report.jar \
	--file-name configuration-cache-report \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.gradle.buildtool.internal/configuration-cache-report.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "configuration-cache-report"' "$idx"
test -s %{buildroot}%{_javadir}/configuration-cache-report.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/configuration-cache-report.jar
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
CORE=%{_javadir}/kotlinx-serialization-core.jar
JSON=%{_javadir}/kotlinx-serialization-json.jar
ANN=%{_javadir}/org.jetbrains.annotations.jar
test -s "$JAR"
mkdir -p check
cat > check/Probe.kt << 'EOF'
import org.gradle.problems.internal.report.HtmlReportWriter
import org.gradle.problems.internal.report.model.JsConfigurationCacheSummary
import org.gradle.problems.internal.report.model.parseCcSummary
import java.io.StringWriter

fun main() {
    val text = "{\"cacheAction\":\"stored\",\"documentationLink\":\"https://docs.gradle.org\",\"totalProblemCount\":1,\"uniqueProblemCount\":1,\"overflownProblemCount\":0}"
    val parsed = parseCcSummary(text)
    val summary = JsConfigurationCacheSummary(
        cacheAction = "stored",
        documentationLink = "https://docs.gradle.org",
        totalProblemCount = 2,
        uniqueProblemCount = 2,
        overflownProblemCount = 0
    )
    val writer = StringWriter()
    val report = HtmlReportWriter(writer)
    report.beginHtmlReport()
    report.endHtmlReport(summary)
    val html = writer.toString()
    if (parsed.cacheAction != "stored" || parsed.totalProblemCount != 1) error("parsed")
    if (!html.contains("<script type=\"application/json\" id=\"diagnostics\">")) error("html")
    println("configuration_cache_report_ok " + parsed.cacheAction + " " + parsed.totalProblemCount + " " + summary.totalProblemCount)
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-cp "$JAR:$STDLIB:$INSTANT:$CORE:$JSON:$ANN" -d check/out check/Probe.kt
java -cp "check/out:$JAR:$STDLIB:$INSTANT:$CORE:$JSON:$ANN" ProbeKt > check/out.txt
cat check/out.txt
grep -F -qx 'configuration_cache_report_ok stored 1 2' check/out.txt

%files -f .mfiles
%license LICENSE
